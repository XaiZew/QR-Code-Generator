# QR-Code-Generator
Simple QR Code Generator using ReedSolomon for data encoding
Basic function, missing Penalty 3 calculation, only ECC rate 7, Version 1 & 2

Dependencies:
- matplotlib
- reedsolo
- numpy
- flask
How to install dependencies if missing:
```
pip install --upgrade reedsolo matplotlib numpy flask
```

How to run:
Open CMD or terminal of your choosing.
Open folder in terminal e.g. if using windows CMD then:
```
cd "path_to_folder"
```
```py
python -u "./server,py"
```
Open index.html
Enter text into input box and click generate, depending on length of characters either version 1 or version 2 will be used for generation.