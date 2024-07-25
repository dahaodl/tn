from flask import Flask, render_template
import os
import stat

app = Flask(__name__,template_folder='templates', static_folder='static')

# Make the WSGI interface available at the top level so wfastcgi can get it.
wsgi_app = app.wsgi_app

FILE_SYSTEM_ROOT = "E:\Automatic-Grading-OpenCV-Python-master\Automatic-Grading-OpenCV-Python-master\static"

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
    return 'something bad happened'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1234)
