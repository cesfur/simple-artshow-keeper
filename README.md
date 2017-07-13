artshow-keeper
==============

Artshow keeper keeps a small Artshow running.

This application allows you to:
* Register items to the Artshow at the consite.
* Import multiple items from a simple e-mail form or CSV (comma separated values) encoded in UTF-8.
* Print A5 bid-sheets. Bidsheet is defined through HTML/CSS and it is customizable.
* Auction selected items. Application can show a show indicating the currently
  processed item at the auction. This screen is defined through HTML/CSS and it is customizable.
* Reconciliate of item owners (hand-out unsold items, retrieve payments, hand-out payments).
  Each reconciliation will print a summary. Printed summary is defined through HTML and
  it is customizable.
* Customize Auction Screen and Bidsheets by supplying corresponding CSS and graphics
  to a folder '%HOME%\AppData\Roaming\artshowkeeper\Custom'. Installer will create a link
  to the folder. Use filenames:
  - StatusFrame.css for the auction screen.
  - Bidsheets.css for a bidsheet.
  Use 300 DPI PNG for best results both in print. For more details about the structure
  of the HTML, open corresponding page in the browser and see the source code. 
  
* Application is ready for international environment:
  - Application is available in English, Czech, and German (partial only).
  - Application can show amounts in other two currencies.
    Currently supported currencies are CZK, EUR, GPB, PLN, USD.
    New currencies can be added upon a request.

*Application has following limitations:
  - Application is optimized for Windows 7 and above, 32-bit only.
  - Application may run on Linux or any other environment which supports Python.
  - Application is a single user application and it is not meant to be used across network.

Installing
* Install Python 3.5.x so that is is accessible from a command line.
* Install Firefox
* Install application. Internet access is required for successful download of libraries.

Running
* The application is client-server system.
* A link on desktop will start server and open a browser (client).
  If the server is already running, only the client will be started.
* Client can be closed any time.
* Server should be closed by pressing Ctr+C. If it is closed by other means, it might leave
  a lock file (%HOME%\AppData\Roaming\artshowkeeper\Data\artshowkeeper.lock) behind. As a result,
  the server will not start. Delete this file to continue.

Configuring
* Find condiguration file '%HOME%\.artshowkeeper.ini' and edit it:
  - Set "DEFAULT_LANGUAGE" to cz, en, or de
  - Set "CURRENCY" to order of currencies. Supported currencies are listed above. Use lower-case, please.
* Start application and select "Settings".
  - Set conversion coefficient.
  - Import CSV with attendees.
