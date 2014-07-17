@echo off
:: Artshow Keeper Tools
:: Copyright (C) 2014  Ivo Hanak
::
:: This program is free software: you can redistribute it and/or modify
:: it under the terms of the GNU General Public License as published by
:: the Free Software Foundation, either version 3 of the License, or
:: (at your option) any later version.
::
:: This program is distributed in the hope that it will be useful,
:: but WITHOUT ANY WARRANTY; without even the implied warranty of
:: MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
:: GNU General Public License for more details.
::
:: You should have received a copy of the GNU General Public License
:: along with this program.  If not, see <http://www.gnu.org/licenses/>.
::

set _AS_ROOTDIR=%ALLUSERSPROFILE%\Artshow
set _AS_LOCKFILE=%_AS_ROOTDIR%\app.lock
set _AS_BACKUPFOLDER=%_AS_ROOTDIR%\remove_all_items_backup
set _AS_ITEMFILE=%_AS_ROOTDIR%\artshowitems.xml

echo Artshow Keeper Tools: Delete all items.
echo.

if exist "%_AS_ROOTDIR%" goto app_installed
echo ERROR: Artshow Keeper is not installed.
goto exit

:app_installed
if not exist "%_AS_LOCKFILE%" goto app_not_running
del "%_AS_LOCKFILE%" 1>NUL 2>NUL
if not exist "%_AS_LOCKFILE%" goto app_not_running
echo ERROR: Artshow Keeper is running. Stop the application (both server and client) and try again.
goto exit
    
:app_not_running
echo Do not run the Artshow Keeper while this script is being executed.
echo.
set /P _AS_DELETE_ALL=Do you want to remove all items (type YES in upper-case to continue)? 
if [%_AS_DELETE_ALL%]==[YES] goto delete_approved
echo Removing cancelled.
goto exit

:delete_approved
if not exist "%_AS_ITEMFILE%.*" goto backup_done
echo.
echo Backing up existing items.
mkdir "%_AS_BACKUPFOLDER%" 1>NUL 2>NUL
copy /Y /V "%_AS_ITEMFILE%.*" "%_AS_BACKUPFOLDER%\" 1>NUL 2>NUL
if errorlevel 0 goto :backup_done
set /P _AS_SKIP_BACKUP=Backup creation has failed. Continue without a backup (type YES in upper-case to continue)? 
if [%_AS_DELETE_ALL%]==[YES] goto backup_done
echo ERROR: Backup creation has failed.
goto exit

:backup_done
echo.
echo Removing all items is irreversible.
set /P _AS_DELETE_ALL=Do you really want to remove all items (type KITTY in upper-case to continue)? 
if [%_AS_DELETE_ALL%]==[KITTY] goto remove
echo Removing cancelled.
goto exit

:remove
echo.
echo Removing existing items.
del /Q "%_AS_ITEMFILE%.*" 1>NUL 2>NUL
if not exist "%_AS_ITEMFILE%.*" goto finished
echo ERROR: Removing all items has failed. Restart you computer or log out/log in and try again.
goto exit

:finished
echo.
echo Items removed.
echo Close this prompt and start the Artshow Keeper.

:exit
echo.
pause
