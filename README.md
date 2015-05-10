artshow-keeper
==============

Artshow keeper keeps a small Artshow running.

This application allows you to:
* Register items to the Artshow at the consite.
* Import multiple items from a simple e-mail form or CSV (comma separated values).
* Print A5 bid-sheets. Bidsheet is defined through SVG and it is customizable.
* Auction selected items. Application can show a show indicating the currently
processed item at the auction. This screen is defined through SVG and it is customizable.
* Reconciliate of item owners (hand-out unsold items, retrieve payments, hand-out payments).
Each reconciliation will print a summary. Printed summary is defined through HTML and
it is customizable.
* Customize Auction Screen and Bidsheets by supplying corresponding CSS and graphics
to a folder '%ALLUSERSPROFILE%/Artshow/custom'. Use filenames:
  - StatusFrame.css for the auction screen.
  - Bidsheets.css for a bidsheet.
  Use SVG for best results both on screen and in print. For more details about the structure
  of the XHTML, open corresponding page in the browser and see the source code. 
  
Application is build with a non-technical users on mind:
* Application compiles to a user friendly Windows MSI installer.

Application is ready for international environment:
* Application is available in English, Czech, and German (partial only).
* Application can show amounts in other two currencies.
Currently supported currencies are CZK, EUR, GPB, PLN, USD.
New currencies can be added upon a request.

Application has following limitations:
* Application is optimized for Windows XP/Vista/7/8.1, 32-bit.
* Application may run on Linux or any other environment which supports Python.
* Application is a single user application and it is not meant to be used across network.
