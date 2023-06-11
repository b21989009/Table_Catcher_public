
# Table Catcher : Extracting Data Tables from Websites

## Documentation:
https://drive.google.com/drive/folders/1xB9fLiRFME2lGquD1h1NbtHFX_4bdvfv?usp=sharing

<br/>

![logo (1)](https://user-images.githubusercontent.com/56702583/209449491-19dc15f7-ab2b-4a9a-8101-a6fc5a574c91.png)

<br />

![Screen Shot 2022-12-24 at 23 22 03](https://user-images.githubusercontent.com/56702583/209450148-78255cc9-17a8-4947-9daa-4743140bfe7a.png)

<br />
<br />

## How to Install On Your Browser:


### Recommended way (with connection to the Backend that is deployed on Azure server):

- download the "extension" folder
- launch Google Chrome and go to chrome://extensions/
- enable developer mode
- click “load unpacked”
- choose “extension” folder
- pin the TableCatcher icon to toolbar. open a website and click the icon.

- ##### (No need for backend installation, since it is deployed and always running on https://tablecatcher.azurewebsites.net .)

<br />
<br />

### Alternatively (Localhost):
#### Run Backend on your computer (localhost):
download the "backend" folder. pycharm (or any IDE) -> open project

In terminal: 
- pip install -r requirements.txt
- python3 manage.py migrate
- python3 manage.py runserver

#### Run the Extension:

- download the "extension" folder
- launch Google Chrome and go to chrome://extensions/
- enable developer mode
- click “load unpacked”
- choose “extension_local” folder
- pin the TableCatcher icon to toolbar. open a website and click the icon.

<br />
<br />
<br />
<br />


Hacettepe University | Computer Engineering Department 
| BBM480 Design Project 

<br />

#### Group Members

Eray Dindaş

Mehmet Giray Nacakcı

Enes Yavuz

<br />

#### Supervisor
Assoc. Prof. BURKAY GENÇ
