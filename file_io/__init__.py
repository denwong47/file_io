#!/usr/bin/env python3

import os, sys, shutil
import json
import hashlib
from datetime import datetime
from uuid import UUID
from typing import Any, Iterable, List, Dict, Union

import asyncio
from async_url import async_url

# from inspect import currentframe, getframeinfo
# from pathlib import Path


# from dictutil import print_dict

class ForInformation(Exception):
    def __bool__(self):
        return True # Note that this is true - this is not an Exception
    __nonzero__ = __bool__
    
#######################################################################################################################################  


class InvalidParameters(ValueError):
    def __bool__(self):
        return False
    __nonzero__ = __bool__

class LocalFolderNotCreatable(RuntimeError):
    def __bool__(self):
        return False
    __nonzero__ = __bool__
    
class LocalFolderNotExistAndCreated(ForInformation):
    pass
    
class LocalFileNotWritable(ValueError):
    def __bool__(self):
        return False
    __nonzero__ = __bool__

class LocalFileNotReadable(ValueError):
    def __bool__(self):
        return False
    __nonzero__ = __bool__

class LocalFileNotRemovable(RuntimeError):
    def __bool__(self):
        return False
    __nonzero__ = __bool__
    
class LocalFileIgnored(ForInformation):
    pass

# This is being used by other modules
class JSONInvalidFormat(ValueError):
    def __bool__(self):
        return False
    __nonzero__ = __bool__

#######################################################################################################################################  
class file():
    path = ""
    isDirectory = False
    isFile = True
    
    def __init__(
        self,
        path:str,
        is_dir:bool=None,
        script_dir:bool=False,
        )->None:

        # Make sure the path is well formed
        if (path.strip() == ".") or (path.strip() == ""):
            path = "./"
        elif (path[0] == "/"): # If path starts from root
            pass
        elif (path[0:2] == "./"):
            pass
        else:
            path = "./" + path
        
        if (script_dir):
            self.path = os.path.join(type(self).get_script_dir(), path)
        else:
            self.path = path
        
        if (is_dir is None):
            if (self.exists()):
                is_dir = os.path.isdir(self.path)
            else:
                is_dir = False # Default Value
                
        self.isDirectory = is_dir
        self.isFile = not is_dir

    def __bool__(self):
        return self.exists()

    @classmethod
    def get_script_dir(self, path=__file__):
        parent = os.path.dirname(sys.argv[0])

        return parent
        
    @classmethod
    def temp(cls,
             path="./",
             prefix="",
             ext=""):
        ext = ("." if (len(ext)>0) else "")+ext.strip(".")
        if (isinstance(path, cls)):
            path = path.path
        
        _time = datetime.utcnow().isoformat()
        _hash = hashlib.md5(_time.encode("utf-8")).hexdigest()
        _filename = prefix+str(UUID(_hash))+ext
        _path = os.path.join(path, _filename)
        return cls(_path, is_dir=False)
    
    @classmethod
    def cwd(cls):
        return cls(os.getcwd())
        
    def __str__(self):
        return "<%s Object at %s>" % ("Directory" if self.isDirectory else "File", self.abspath())
    
    def name(self):
        return os.path.basename(self.path)
    
    def abspath(self):
        _abspath = os.path.abspath(self.path)
        
        return _abspath
    
    def exists(self):
        return os.path.exists(self.path)
    
    def size(self):
        if (self.exists() and self.isFile):
            return os.path.getsize(self.path)
        else:
            return None

    def handle(self, mode):
        return open(self.abspath(), mode)
        
    def isreadable(self):
        return check_file_readable(self.path)
    
    def iswritable(self):
        return check_file_writable(self.path)
    
    def remove(self):
        if (self.exists()):
            if (self.isDirectory):
                try:
                    shutil.rmtree(self.path)
                    return True
                except Exception as e:
                    return LocalFileNotRemovable("Directory %s cannot be removed, error \"%s\"." % (self.abspath()))
            else:
                try:
                    os.remove(self.path)
                    return True
                except Exception as e:
                    return LocalFileNotRemovable("File %s cannot be removed, error \"%s\"." % (self.abspath()))
        else:
            return InvalidParameters("File %s does not exists, cannot be removed." % (self.abspath()))
                    
    
    delete = remove
    
    def read(self, output=str):
        if (self.isreadable()):
            with open(self.path, "r" + ("+b" if output is bytes else "")) as _f:
                _contents = _f.read()
                _f.close()

            if (output is dict):
                try:
                    _json = json.loads(_contents)
                    _contents = _json
                except Exception as e:
                    pass
                
            return _contents
        else:
            return LocalFileNotReadable("File %s is not readable." % (self.abspath()))
        
    def readlines(self, strip_lines = True):
        _contents = None
        if (self.isreadable()):
            with open(self.path, "r") as _f:
                _contents = _f.readlines()
                _f.close()
            
            if (strip_lines):
                _contents = [_line.rstrip("\n") for _line in _contents]
            return _contents
        else:
            return LocalFileNotReadable("File %s is not readable." % (self.abspath()))
        
    def parent(self):
        _path = self.abspath()
        if (self.isDirectory and _path[-1] == "/"):
            _path = _path[:-1]
        else:
            _path = _path
            
        _parent_path = os.path.dirname(_path)
            
        return file(_parent_path, is_dir = True)
    
    def child(self, path, is_dir=None):
        return self.__class__(os.path.join(self.path, path), is_dir=is_dir)
        
    # Creates the whole directory hierarchy if it doesn't exist
    def build_tree(self):
        
        if (not self.exists()):
            _parent = self.parent()

            if (not _parent.exists()):
                _result = _parent.build_tree()
                if (not _result):
                    return _result

            if (self.isDirectory):
                try:
                    os.mkdir(self.abspath())
                except OSError as e:
                    return LocalFileNotWritable("Directory %s cannot be created." % (self.path))

                return True
            else:
                if (self.iswritable()):
                    return True
                else:
                    return LocalFileNotWritable("Directory to File %s is present, but the file itself is not writable." % (self.path))
        else:
            return True
        
    def save(self, contents, overwrite=True):
        _type_switch = {
            None: lambda contents: contents,
            bytes: lambda contents: contents,
            dict: lambda contents: json.dumps(contents, indent=4, default=str),
            list: lambda contents: "\n".join(contents)
        }
        
        if (not self.iswritable()):
            _result = self.build_tree()
            
            if (not _result):
                return _result
        
        if (self.iswritable()):
            with open(self.path, ("w" if overwrite else "a") + ("+b" if type(contents) is bytes else "")) as _f:
                _f.write(_type_switch.get(type(contents), _type_switch[None])(contents))
                _f.close()
                return True
        else:
            return LocalFileNotWritable("File %s is not writable." % (self.path))
        
    write=save # alias
        
    def touch(self):
        if (not self.exists()):
            return self.save(b"")
        else:
            return True

    # Read directory tree of local folder
    def dir_tree(self,
                 ignore_list=[],
                 ignore_dotted=True,
                 sub_directories=True,
                 flatten=False,
                )->Iterable["file"]:
        path = self.path
            
        if (self.exists()):
            if (os.path.isdir(path) and self.isDirectory):

                # Make a prefix so we can make keys for dict
                _path_prefix = path + ("/" if path[-1] != "/" else "")

                # Automatically ignore /. and /.. where reported by system
                ignore_list += [".", ".."]

                if (os.path.isdir(path)):
                    _dir_tree = {}

                    if (self.isreadable()):
                        self.isreadable()

                        for _file_path in os.listdir(path):

                            if (os.path.basename(_file_path).lower() in ignore_list or \
                                (ignore_dotted and os.path.basename(_file_path)[0] == ".")
                            ):
                                # Ignored entry
                                pass
                            else:
                                if (os.path.isdir(_path_prefix+_file_path)):
                                    _current_dir = file(_path_prefix+_file_path)
                                    
                                    if (sub_directories):
                                        _sub_dir = _current_dir.dir_tree(ignore_list=ignore_list,
                                                                        ignore_dotted=ignore_dotted,
                                                                        flatten=flatten)
                                    else:
                                        _sub_dir = {}

                                    if (flatten):
                                        _dir_tree[_path_prefix+_file_path] = _current_dir
                                        _dir_tree = {**_dir_tree, **_sub_dir}
                                    else:
                                        _dir_tree[_path_prefix+_file_path] = {".": _current_dir,
                                                                **_sub_dir}
                                else:
                                    _dir_tree[_path_prefix+_file_path] = file(_path_prefix+_file_path)
                    else:
                        # Permission denied, folder cannot be listed
                        _dir_tree = {
                            ".":LocalFileNotReadable(f"Permission Denied while trying to list contents of {self.abspath()}.")
                        }

                    return _dir_tree
            
            else:
                return InvalidParameters("Path %s is not a directory." % (path))
        else:
            return InvalidParameters("Path %s does not exists." % (path))
    
    # Copy Directory/File to another location.
    # examples:
    # - file(./a.txt) to file(./new_location/b.txt)                                                   a.txt will be copied to a subdirectory with a new name
    # - file(./a.txt) to file(./new_location, is_dir=False)                                           a.txt will be copied to a new file named new_location
    # - file(./a.txt) to file(./new_location, is_dir=True)                                            a.txt will be copied to a subdirectory with its existing name
    # - file(./dir, is_dir=True) to file(./new_dir, is_dir=True)           copy_to_base_dir=False     /dir will be copied to /new_dir/dir with all sub-directories
    # - file(./dir, is_dir=True) to file(./new_dir, is_dir=True)           copy_to_base_dir=True      /dir will be copied to /new_dir with all sub-directories
    # - file(./dir, is_dir=True) to file(./new_dir, is_dir=False)          copy_to_base_dir=False     /dir will be copied to / with all sub-directories
    # - file(./dir, is_dir=True) to file(./new_dir/new.file, is_dir=True)  copy_to_base_dir=True      /dir will be copied to /new_dir/new.file (new.file is a directory) with all sub-directories
    # - file(./dir, is_dir=True) to file(./new_dir/new.file, is_dir=False) copy_to_base_dir=True      /dir will be copied to /new_dir with all sub-directories
    
    def copy_to(self,
                target_path,
                ignore_list=[],
                ignore_dotted=False,
                copy_to_base_dir=True,
                sub_directories=True,
                echo=False,
               ):
        
        if (not isinstance(target_path, file)):
            # Detect automatically whether its a directory or not
            target_path = file(path=target_path, is_dir=None)
        
        _dest_name = os.path.basename(self.path)
        
        
        if (not "." in ignore_list):
            ignore_list.append(".")
        
        if (not ".." in ignore_list):
            ignore_list.append("..")
        
        if (not os.path.basename(self.path) in ignore_list):
            
            if (ignore_dotted or os.path.basename(self.path)[0] != "."):
                
                _log = {}

                if echo: print ("Copying %s to %s" % (self, target_path))

                # if its a file, get the directory instead
                if (target_path.isFile):
                    if (self.isFile):
                        _dest_name = os.path.basename(target_path.path)

                    target_path = file(path=os.path.dirname(target_path.path), is_dir=True)

                if (self.isDirectory):
                    _dir_tree = self.dir_tree(
                        ignore_list=ignore_list,
                        ignore_dotted=ignore_dotted,
                        sub_directories=False,
                        flatten=True,
                    )

                    if (copy_to_base_dir):
                        _dest_dir = file(target_path.path, is_dir=True)
                    else:
                        _dest_dir = file(os.path.join(target_path.path, _dest_name), is_dir=True)
                        
                    affirm_folder_exists (_dest_dir.path)

                    for _file in _dir_tree:
                        if (sub_directories or not _dir_tree[_file].isDirectory):
                            _result = _dir_tree[_file].copy_to(_dest_dir,
                                                              ignore_list=ignore_list,
                                                              ignore_dotted=ignore_dotted,
                                                              sub_directories=sub_directories,
                                                              copy_to_base_dir=False,
                                                             )
                            
                            if (isinstance(_result, dict)):
                                _log = {**_log, **_result}
                            else:
                                _log[_file] = _result
                        else:
                            # It is a sub-directory and sub-directories is False
                            _log[_file] = LocalFileIgnored("Directory %s is a sub-directory and thus ignored." % (_file))
                        
                    return _log
                else:
                    affirm_folder_exists(target_path.path)
                    shutil.copy(self.path, os.path.join(target_path.path, _dest_name))
                    return True
                    
            else:
                _result = "File %s is a Unix hidden file and thus ignored." % (self.path)
                if echo: print(_result)
                return LocalFileIgnored(_result)
                
        else:
            _result = "File %s is a Unix hidden file and thus ignored." % (self.path)
            if echo: print (_result)
            return LocalFileIgnored(_result)

    @classmethod
    def wget(cls, loc:str, path:str, *args, **kwargs):
        _data = asyncio.run(async_url.wget(loc, *args, **kwargs))

        if (not isinstance(_data, Exception)):
            _file = cls(path, is_dir=False)
            if (_file.iswritable()):
                _file.write(_data)
                return _file
            else:
                
                return LocalFileNotWritable(f"File {path} is not writable.")
        else:
            # Exception, return
            return _data

#######################################################################################################################################


# █▀▀ █░█ █▀▀ █▀▀ █▄▀   █▀▀ █ █░░ █▀▀   █▀█ █▀▀ ▄▀█ █▀▄ ▄▀█ █▄▄ █░░ █▀▀
# █▄▄ █▀█ ██▄ █▄▄ █░█   █▀░ █ █▄▄ ██▄   █▀▄ ██▄ █▀█ █▄▀ █▀█ █▄█ █▄▄ ██▄

def check_file_readable(file_path):
    if os.path.exists(file_path):
        # path exists
        if os.path.isfile(file_path):
            return os.access(file_path, os.R_OK)
        else:
            try:
                _void = os.listdir(file_path)
                return True
            except PermissionError as e:
                return False
    
    return False

#######################################################################################################################################

# █▀▀ █░█ █▀▀ █▀▀ █▄▀   █▀▀ █ █░░ █▀▀   █░█░█ █▀█ █ ▀█▀ ▄▀█ █▄▄ █░░ █▀▀
# █▄▄ █▀█ ██▄ █▄▄ █░█   █▀░ █ █▄▄ ██▄   ▀▄▀▄▀ █▀▄ █ ░█░ █▀█ █▄█ █▄▄ ██▄

def check_file_writable(file_path):
    if os.path.exists(file_path):
        # path exists
        if os.path.isfile(file_path): # is it a file or a dir?
            # also works when file is a link and the target is writable
            return os.access(file_path, os.W_OK)
        else:
            return False # path is a dir, so cannot write as a file
    # target does not exist, check perms on parent dir
    dir_path = os.path.dirname(file_path)
    if not dir_path: dir_path = '.'
    # target is creatable if parent dir is writable
    return os.access(dir_path, os.W_OK)

#######################################################################################################################################

# ▄▀█ █▀▀ █▀▀ █ █▀█ █▀▄▀█   █▀▀ █▀█ █░░ █▀▄ █▀▀ █▀█   █▀▀ ▀▄▀ █ █▀ ▀█▀ █▀
# █▀█ █▀░ █▀░ █ █▀▄ █░▀░█   █▀░ █▄█ █▄▄ █▄▀ ██▄ █▀▄   ██▄ █░█ █ ▄█ ░█░ ▄█

def affirm_folder_exists(folder_path, check_writable=True):
    
    if not folder_path: folder_path = '.'
        
    _folder_created = False
    
    # Create if not exists
    if (not os.path.exists(folder_path)):
        try:
            os.makedirs(folder_path)
            _folder_created = True
        except Exception as e:
            return LocalFolderNotCreatable(str(e))
    
    # Check if folder is writable
    if (os.path.isdir(folder_path)):
        if (check_writable):
            _folder_writable = os.access(folder_path, os.W_OK)
            if (_folder_created and _folder_writable):
                # Its not actually an exception
                return LocalFolderNotExistAndCreated("Folder created")
            else:
                return _folder_writable
        else:
            return True
    else:
        # This can generate a false alarm being there is a file that already exists under that name but you actually wanted a folder with the same name. Bad practice anyway - will fix later.
        return False

       


# In[ ]:


# Debug Test
if __name__=="__main__":
#     _file = file("../update_cache/a2dfhjr/fshjk.file")
#     print (_file.save("Testing 123\nNew line 456"))
    _folder = file.cwd().child("temp", is_dir=True)

    for _count in range(100):
        print (file.temp(_folder).touch())
#     print (_file.abspath())
#     print (_file.touch())

#     _from = file("./update_cache")
#     _to = file("./copy_to/test.dir", is_dir = True)

#     print_dict(_from.copy_to(_to, copy_to_base_dir=False), direct_output = True)


# In[ ]:







# Created by convert_to_py at 2021-07-04T16:58:26.458026.