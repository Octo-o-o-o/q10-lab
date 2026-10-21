@echo off
REM Official bbndk-env_*.bat is not in the IA tools/libraries zips.
REM QNX_HOST + QNX_TARGET + PATH are enough for qcc -V; the rest match published env bats.
set "QNX_BASE=C:\q10-lab\ndk\bbndk"
set "QNX_HOST=%QNX_BASE%\host_10_3_1_12\win32\x86"
set "QNX_TARGET=%QNX_BASE%\target_10_3_1_995\qnx6"
set "QNX_CONFIGURATION=%LOCALAPPDATA%\Research In Motion\BlackBerry Native SDK"
set "MAKEFLAGS=-I%QNX_TARGET%\usr\include"
set "CPUVARDIR=armle-v7"
set "PATH=%QNX_HOST%\usr\bin;%PATH%"
