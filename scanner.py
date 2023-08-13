import PySimpleGUI as sg
import cv2
import numpy as np
from pyzbar.pyzbar import decode, ZBarSymbol
import mysql.connector
import io
from PIL import Image
from subprocess import call


# Create video capture
def video_capture():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    #cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    #cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
    #cap.set(cv2.CAP_PROP_FPS, 30)
    return cap

# Update keypad
def update_code(keytype):
    if keytype == "ENTER":
        if len(values['-INPUT-']) > 3:
            search_barcode(values['-INPUT-'])
    elif keytype == "DELETE":
        HomeWindow['-INPUT-'].update(values['-INPUT-'][:-1])
    else:
        HomeWindow['-INPUT-'].update(values['-INPUT-'] + keytype)

# Perform a search when the length of the input is 6 characters
def auto_complete():
    if len(values['-INPUT-']) == 6:
        search_barcode(values['-INPUT-'])

# Search code in database
def search_barcode(code):
    HomeWindow['-INPUT-'].update("")
    reading = False
    cur = db.cursor()
    cur.execute("SELECT ID FROM products WHERE CODE LIKE \'%"+ code +"%\'")
    results = cur.fetchall()
    records = cur.rowcount
    if records == 0:
        not_found()
    elif records == 1:
        for result in results:
            product(result[0])
    else:
        showrecord(code)

# Query product information
def product(id):
    global cap
    cap.release()
    cur = db.cursor()
    cur.execute("SELECT products.CODE, products.NAME, products.PRICESELL, products.CATEGORY, products.IMAGE, categories.NAME FROM products, categories WHERE products.ID=\'"+ id +"\' AND products.CATEGORY = categories.ID")
    exist = cur.fetchone()
    if exist is None:
        not_found()
    else:
        if exist[4] is None:
            image = Image.open('picture/empty.png')
        else:
            image = Image.open(io.BytesIO(exist[4]))
        image = image.resize((300, 300), Image.LANCZOS)
        bImage = io.BytesIO()
        image.save(bImage, format="PNG")
        
        col1 = [
                [sg.Image(data=bImage.getvalue())],
               ]
        col2 = [
                [sg.Text(key='-SPACER1-', font='ANY 1', pad=(0, 0))],
                [sg.Text(exist[1], font=('Arial', 40, 'bold'), text_color='#2ea062', pad=(20, 40))],
                [sg.Text("Code: "+ exist[0], font='Arial 25', text_color='grey')],
                [sg.Text("Category: "+ exist[5], font='Arial 25', text_color='grey')],
                [sg.Text(key='-SPACER2-', font='ANY 1', pad=(0, 0)), sg.Text('$%.2f' % exist[2], font=('Arial', 100, 'bold'), text_color='#2ea062', justification='center', pad=(0, 20)), sg.Text(key='-SPACER3-', font='ANY 1', pad=(0, 0))]
               ]
        layout = [[sg.Column(col1), sg.Column(col2)]]

        window = sg.Window('PRODUCT', layout, element_justification='c', modal=True, no_titlebar=True, location=(0,0), size=(screen_width, screen_height), keep_on_top=True).Finalize()
        window.Maximize()
        window.bind("<Button-1>", 'Window Click')
        window['-SPACER1-'].expand(True, True, True)
        window['-SPACER2-'].expand(True, True, True)
        window['-SPACER3-'].expand(True, True, True)
        while True:
            event, values = window.read(timeout=6000)
            if event == sg.WIN_CLOSED or event == 'Window Click' or event == sg.TIMEOUT_KEY:
                break
        cap = video_capture()
        window.close()

# Display multiple products in atable
def showrecord(code):
    global cap
    cap.release()
    cur = db.cursor()
    cur.execute("SELECT products.NAME, categories.NAME, products.PRICESELL FROM products, categories WHERE products.CODE LIKE \'%"+ code +"%\' AND products.CATEGORY = categories.ID ORDER BY categories.NAME, products.NAME LIMIT 10")
    data = cur.fetchall()
    header_list = ["NAME", "CATEGORY", "PRICE($)"]
    if data is None:
        not_found()
    else:
        for index, item in enumerate(data):
            itemlist = list(item)
            itemlist[2] = '$%.2f' % itemlist[2]
            item = tuple(itemlist)
            data[index] = item
        sg.set_options(element_padding=(0, 0))
        layout = [
                    [sg.Text(key='-SPACER1-', font='ANY 1', pad=(0, 0))],
                    [sg.Text('More than one products(s) were found', font=('Arial', 28), text_color='#2ea062', justification='center', pad= ((65, 0), (0, 16)))],
                    [sg.Table(
                        key='Table',
                        values=data, 
                        headings=header_list,
                        col_widths=[27, 13, 8],
                        auto_size_columns=False,
                        justification=('lef'),
                        # alternating_row_color='lightblue',
                        num_rows=min(len(data), 10),
                        font=('monospace', 20))
                    ],
                    [sg.Text(key='-SPACER2-', font='ANY 1', pad=(0, 0))]
                 ]
        window = sg.Window('ShowRecords', layout, grab_anywhere=False, modal=True, no_titlebar=True, location=(0,0), size=(screen_width, screen_height), keep_on_top=True).Finalize()
        window.Maximize()
        window.bind("<Button-1>", 'Window Click')
        window['-SPACER1-'].expand(True, True, True)
        window['-SPACER2-'].expand(True, True, True)
        window['Table'].Widget.column('#2', anchor='c')
        window['Table'].Widget.column('#3', anchor='e') # east for right
        while True:
            event, values = window.read(timeout=12000)
            if event == sg.WIN_CLOSED or event == 'Window Click' or event == sg.TIMEOUT_KEY:
                break
        cap = video_capture()
        window.close()

# Not found page
def not_found():
    global cap
    cap.release()
    layout = [
                [sg.Text(key='-SPACER1-', font='ANY 1', pad=(0, 0))],
                [sg.Image(filename='picture/notfound.png')],
                [sg.Text('PRODUCT NOT FOUND !!!', font='Arial 36', text_color='#2ea062', justification='center', pad=(0, 30))],
                [sg.Text(key='-SPACER2-', font='ANY 1', pad=(0, 0))]
             ]
    window = sg.Window('NOT FOUND', layout, element_justification='c', modal=True, no_titlebar=True, location=(0,0), size=(screen_width, screen_height), keep_on_top=True).Finalize()
    window.Maximize()
    window.bind("<Button-1>", 'Window Click')
    window['-SPACER1-'].expand(True, True, True)
    window['-SPACER2-'].expand(True, True, True)
    while True:
        event, values = window.read(timeout=3000)
        if event == sg.WIN_CLOSED or event == 'Window Click' or event == sg.TIMEOUT_KEY:
            break
    cap = video_capture()
    window.close()

# APPLICATION (GUI)
screen_width = 800
screen_height = 480
b_x = 100
b_y = 180
b_w = 280
b_h = 150
b_pts = np.array([[b_x,b_y],[b_x,b_y+b_h],[b_x+b_w,b_y+b_h],[b_x+b_w,b_y]], np.int32)
# Enter your host, user, and password for your database server
db = mysql.connector.connect(host="localhost", user="root", passwd="adminmonsung", db="chromispos")
cap = video_capture()
sg.theme('GreenMono')

# ------------------------------------ HOME WINDOW ------------------------------------- #
col = [
        [sg.Image(filename='picture/guide.png')],
        [sg.Text('Enter last 6 digits', font='Arial 26', text_color='#2ea062', justification='center')],
        [sg.Input(justification='center', key='-INPUT-', font='Andale 32', background_color='#6ba284', text_color='#efffff')],
        [sg.Button(' 1 '), sg.Button(' 2 '), sg.Button(' 3 ')],
        [sg.Button(' 4 '), sg.Button(' 5 '), sg.Button(' 6 ')],
        [sg.Button(' 7 '), sg.Button(' 8 '), sg.Button(' 9 ')],
        [sg.Button(' ⌫ '), sg.Button(' 0 '), sg.Button(' ⎆ ')]
      ]

HomeLayout = [[sg.Image(filename='', key='preview'), sg.Column(col)]]
HomeWindow = sg.Window('SCANNER', HomeLayout, no_titlebar=True, location=(0,0), size=(screen_width, screen_height), keep_on_top=False, font=('monospace', 23)).Finalize()
#HomeWindow.Maximize()
#HomeWindow = sg.Window('SCANNER', HomeLayout, no_titlebar=True, location=(0,0), size=(screen_width, screen_height), font=('monospace', 24)).Finalize()

# PROCESSING
while True:
    event, values = HomeWindow.read(timeout=1)
    if event == sg.WIN_CLOSED or values['-INPUT-'] == "666666":
        break
    elif values['-INPUT-'] == "555":
        #call(["/usr/bin/vcgencmd", "display_power", "0"])
        #call('xset dpms force off', shell=True)
        continue
    elif event == ' 0 ':
        update_code("0")
    elif event == ' 1 ':
        update_code("1")
    elif event == ' 2 ':
        update_code("2")
    elif event == ' 3 ':
        update_code("3")
    elif event == ' 4 ':
        update_code("4")
    elif event == ' 5 ':
        update_code("5")
    elif event == ' 6 ':
        update_code("6")
    elif event == ' 7 ':
        update_code("7")
    elif event == ' 8 ':
        update_code("8")
    elif event == ' 9 ':
        update_code("9")
    elif event == ' ⌫ ':
        update_code("DELETE")
    elif event == ' ⎆ ':
        update_code("ENTER")
    auto_complete()

    # Scanning
    ret, img = cap.read()
    img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    
    for barcode in decode(img, symbols = [ZBarSymbol.EAN13, ZBarSymbol.EAN8, ZBarSymbol.UPCE, ZBarSymbol.CODE128, ZBarSymbol.CODE93, ZBarSymbol.CODE39]):
        read_code = barcode.data.decode('utf-8')
        if barcode.type == "EAN13" and read_code.startswith("0"):
            read_code = read_code[1:]
        search_barcode(read_code)
    cv2.putText(img, "SCAN BARCODE", (90, 90), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (98, 160, 46), 2)
    cv2.polylines(img, [b_pts], True, (98, 160, 46), 2)
    #cv2.line(img, (b_x-40, b_y+(b_h//2)), (b_x+b_w+40, b_y+(b_h//2)), (0, 160, 0), 2)
    #cv2.putText(img, "$", (220, 420), cv2.FONT_HERSHEY_SIMPLEX, 2, (98, 160, 46), 2)
    imgbytes = cv2.imencode('.png', img)[1].tobytes()
    HomeWindow['preview'].update(data=imgbytes)
    cv2.waitKey(1)

# CLOSE
db.close()
cap.release()
HomeWindow.close()
#call(["/usr/bin/vcgencmd", "display_power", "1"])
#call('xset dpms force on', shell=True)