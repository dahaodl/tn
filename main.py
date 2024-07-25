from flask import Flask, render_template,request,redirect, url_for, send_from_directory,session
from werkzeug.utils import secure_filename
from flask_session import Session
from grade_paper import ProcessPage
from process_img import processImageBGD
import cv2
import pandas as pd
import csv
import os
import numpy as np
import glob
import csv as csv1
import serial

'''ser = serial.Serial(
    port='COM4',
    baudrate=9600,
    parity=serial.PARITY_ODD,
    stopbits=serial.STOPBITS_TWO,
    bytesize=serial.SEVENBITS
)

ser.timeout = 2
ser.xonxoff = False     #disable software flow control
ser.rtscts = False     #disable hardware (RTS/CTS) flow control
ser.dsrdtr = False       #disable hardware (DSR/DTR) flow control
ser.writeTimeout = 2 '''
 
cc = 0
charArray = []
answersArray = []
USERNAME = "admin"
PASSWORD = "admin"
app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
app.secret_key = os.getenv("SECRET", "not a secret")
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ALLOWED_EXTENSIONS'] = set(['png', 'jpg', 'jpeg'])
wsgi_app = app.wsgi_app
FILE_SYSTEM_ROOT = "E:\Automatic-Grading-OpenCV-Python-master\Automatic-Grading-OpenCV-Python-master\static\chamtn"

@app.route('/', methods=['GET', 'POST'])
def get_signin():
    return redirect('/main')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

@app.route('/main', methods=['GET', 'POST'])
def main():
    return render_template("main.html")

@app.route('/bridge', methods=['GET','POST'])
def bridge():
    if request.method=="POST":
        if request.form['check']=="hangloat":
            return redirect('/chamhangloat')
        if request.form['check']=="start":
            return redirect('/chamthi')
        elif request.form['check']=="startbgd":
            return redirect('/chamthibgd')
        elif request.form['check']=="csv":
            return redirect('/csv')
        elif request.form['check']=="browserfile":
            return redirect('/browser')
        else:
            return redirect('/')
    else:
        return redirect('/')

@app.route('/chamthi',methods=['GET', 'POST'])
def index():
    return render_template('point.html')

@app.route('/chamthibgd',methods=['GET', 'POST'])
def indexbgd():
    #import time
    #ser.write(b'5')
    #time.sleep(1)
    #print("Keo giay")
    return render_template('pointbgd.html')

@app.route('/csv',methods=['GET', 'POST'])
def csv():
    return render_template('csv.html')

@app.route('/dashboardcsv', methods=['POST'])
def dashboardcsv():
        file = request.files['file']
        file.save("db/dapan.csv")
        num = []
        char = []
        with open("db/dapan.csv", newline='') as f:
                reader = csv1.reader(f)
                for row in reader:
                        num.append(row[0])
                        char.append(row[1])
        charArray = char
        return render_template('dashboardcsv.html', num = num, lres = char)

@app.route('/dashboard', methods=['POST'])
def dashboard():
        global charArray
        file = request.files['file']
        if file and allowed_file(file.filename):
                file.save("static/tracnghiem.png")

        def clockwise_sort(x):
                return (np.arctan2(x[0] - mx, x[1] - my) + 0.5 * np.pi) % (2*np.pi)

        image = cv2.imread("static/tracnghiem.png")
        ratio = len(image[0]) / 500.0
        original_image = image.copy()
        image = cv2.resize(image, (0,0), fx=1/ratio, fy=1/ratio)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.bilateralFilter(gray, 11, 17, 17)
        edged = cv2.Canny(gray, 250, 300)
        temp_img, contours = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(temp_img, key=cv2.contourArea, reverse=True)[:10]
        biggestContour = None
        for contour in contours:
                peri = cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
                if len(approx) == 4:
                        biggestContour = approx
                        break
        points = []
        desired_points = [[0,0], [425, 0], [425, 550], [0, 550]]
        desired_points = np.float32(desired_points)
        if biggestContour is not None:
                for i in range(0, 4):
                        points.append(biggestContour[i][0])
        mx = sum(point[0] for point in points) / 4
        my = sum(point[1] for point in points) / 4
        points.sort(key=clockwise_sort, reverse=True)
        points = np.float32(points)
        paper = []
        points *= ratio
        answers = 1
        if biggestContour is not None:
                M = cv2.getPerspectiveTransform(points, desired_points)
                paper = cv2.warpPerspective(original_image, M, (425, 550))
                answers, paper = ProcessPage(paper)
                answersArray = answers
                cv2.imwrite("static/kq.png", paper)
        num = []
        char = []
        with open("db/dapan.csv", newline='') as f:
                reader = csv1.reader(f)
                for row in reader:
                        num.append(row[0])
                        char.append(row[1])
        charArray = char
        lres = []
        compareArray = []
        count = 0
        for i in range(min(len(answersArray), len(charArray))):
            if (answersArray[i] != charArray[i]):
                compareArray.append("Sai")
            else:
                compareArray.append("Dung")
                count = count + 1
        print(answersArray)
        print(charArray)
        return render_template('dashboard.html', user_image = "static/kq.png", length = min(len(answersArray), len(charArray)),
                               answersArray = answersArray, charArray = charArray, compareArray = compareArray, count = count)

@app.route('/dashboardbgd', methods=['POST'])
def dashboardbgd():
        global cc
        file = request.files['file']
        if file and allowed_file(file.filename):
                file.save("static/tracnghiem.png")
        image = cv2.imread("static/tracnghiem.png")
        error = []
        dictArray = processImageBGD(image)
        answerArray = []
        for i in range(len(dictArray)):
            if (len(dictArray[i]) >= 1): answersArray.append(dictArray[i][0])
            if len(dictArray[i]) > 1 or len(dictArray) == 0: error.append(i)
        num = []
        char = []
        with open("db/dapan.csv", newline='') as f:
                reader = csv1.reader(f)
                for row in reader:
                        num.append(row[0])
                        char.append(row[1])
        charArray = char
        lres = []
        compareArray = []
        count = 0
        for i in range(min(len(answersArray), len(charArray))):
            if (answersArray[i] != charArray[i]):
                compareArray.append("Sai")
            else:
                compareArray.append("Dung")
                count = count + 1
        print(answersArray)
        print(charArray)
        cc = cc + 1
        if (len(error) > 0):
            cv2.imwrite("/static/chamtn/anhsua/" + str(cc) + ".png", image)
        cv2.imwrite("/static/chamtn/anhcham/" + str(cc) + ".png", image)
        return render_template('dashboardbgd.html', user_image = "static/tracnghiem.png", length = min(len(answersArray), len(charArray)),
                               answersArray = answersArray, charArray = charArray, compareArray = compareArray, count = count, error = error, lengthError = len(error))

@app.route('/chamhangloat', methods=['GET', 'POST'])
def chamhangloat():
        import os
        import csv
        global cc
        path = 'static/chamhangloat/'
        html_files = []
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                html_files.append(os.path.join(dirpath, filename))
        import random
        cc = random.randint(3, 1000)
        try:
            os.remove("static/ketqua.csv")
        except: pass
        for html_file in html_files:
            image = cv2.imread(html_file)
            error = []
            dictArray = processImageBGD(image)
            answerArray = []
            for i in range(len(dictArray)):
                if (len(dictArray[i]) >= 1): answersArray.append(dictArray[i][0])
                if len(dictArray[i]) > 1 or len(dictArray) == 0: error.append(i)
            num = []
            char = []
            with open("db/dapan.csv", newline='') as f:
                    reader = csv1.reader(f)
                    for row in reader:
                            num.append(row[0])
                            char.append(row[1])
            charArray = char
            lres = []
            compareArray = []
            count = 0
            for i in range(min(len(answersArray), len(charArray))):
                if (answersArray[i] != charArray[i]):
                    compareArray.append("Sai")
                else:
                    compareArray.append("Dung")
                    count = count + 1
            print(answersArray)
            print(charArray)
            if (len(error) > 0):
                cv2.imwrite("/static/chamtn/anhsua/" + str(cc) + ".png", image)
            cv2.imwrite("/static/chamtn/anhcham/" + str(cc) + ".png", image)
            
            Our_list = [answersArray, charArray, compareArray]
            with open("static/ketqua.csv", "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerows(Our_list)
                writer.writerows([[str("Tong so cau: ") + str(count)],
                                                                [str("So cau sai") + str(error[0])], [str("So cau nghi ngo") + str(len(error))]])
                writer.writerows([["Bai thi"],["."],["."]])
        
        
        return render_template('pointbgd.html')
    
@app.route('/browser')
def browse():
    itemList = os.listdir(FILE_SYSTEM_ROOT)
    return render_template('browse.html', itemList=itemList)

@app.route('/browser/<path:urlFilePath>')
def browser(urlFilePath):
    nestedFilePath = os.path.join(FILE_SYSTEM_ROOT, urlFilePath)
    if os.path.isdir(nestedFilePath):
        itemList = os.listdir(nestedFilePath)
        fileProperties = {"filepath": nestedFilePath}
        if not urlFilePath.startswith("/"):
            urlFilePath = "/" + urlFilePath
        return render_template('browse.html', urlFilePath=urlFilePath, itemList=itemList)
    if os.path.isfile(nestedFilePath):
        fileProperties = {"filepath": nestedFilePath}
        sbuf = os.fstat(os.open(nestedFilePath, os.O_RDONLY)) #Opening the file and getting metadata
        fileProperties['type'] = stat.S_IFMT(sbuf.st_mode) 
        fileProperties['mode'] = stat.S_IMODE(sbuf.st_mode) 
        fileProperties['mtime'] = sbuf.st_mtime 
        fileProperties['size'] = sbuf.st_size 
        if not urlFilePath.startswith("/"):
            urlFilePath = "/" + urlFilePath
        return render_template('file.html', currentFile=nestedFilePath, fileProperties=fileProperties)
    return 'viniciusbruyne'

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

app.run(host = '0.0.0.0',port = 5005)

