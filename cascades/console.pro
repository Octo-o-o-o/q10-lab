APP_NAME = console
TEMPLATE = app
CONFIG += qt warn_on cascades10 device
QT += network
CODECFORSRC = UTF-8
CODECFORTR = UTF-8
SOURCES += src/main.cpp src/applicationui.cpp
HEADERS += src/applicationui.hpp
INCLUDEPATH += src
LIBS += -lbbdata
QMAKE_CXXFLAGS += -finput-charset=UTF-8
# NDK host `rm` / `ln` hang on this Windows box; use cmd builtins.
QMAKE_DEL_FILE = del /q
QMAKE_MOVE = move /y
QMAKE_LN_SHLIB = copy /y
