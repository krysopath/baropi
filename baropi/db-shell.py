#!/usr/bin/env python3
# coding=utf-8
import baropi as b
import code
import readline

db = b.db_session

if __name__ == "__main__":
    b.init_db()
    var = globals().copy()
    var.update(locals())
    code.InteractiveConsole(var).interact()