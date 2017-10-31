from random import random
import os
import dropbox
import pickle

class NotificationLine:
    def __init__(self, chat_id, freq, message, internal_id):
        self.chat_id = chat_id
        self.frequency = freq
        self.message = message
        self.internal_id = internal_id
        
    def __str__(self):
        return "{:d} {:.16f} {:s} {:d}" \
            .format(self.chat_id, self.frequency, self.message, self.internal_id)

class TimeSystem:
    def __init__(self, file_system):
        self.files = file_system
        self.user_lines = {}
        self.lines = {}
        
        for line in self.files:
            self._push_line(line)
        
        if len(self.lines):
            self.max_internal_id = max(self.lines.keys())
        else:
            self.max_internal_id = 0
            
    def _push_line(self, line):
        self.lines[line.internal_id] = line
        if line.chat_id not in self.user_lines:
            self.user_lines[line.chat_id] = []
            
        self.user_lines[line.chat_id].append(line)
        
    def _pop_line(self, line):
        if isinstance(line, int):
            if line not in self.lines:
                return False
            line = self.lines[line]
        
        del self.lines[line.internal_id]
        self.user_lines[line.chat_id].remove(line)
        
        return True

    def get_line(self, iid):
        return self.lines.get(iid, None)
    
    def get_user_lines(self, chat_id):
        return self.user_lines.get(chat_id, [])
    
    def register_line(self, chat_id, frequency, message):
        self.max_internal_id += 1
        line = NotificationLine(chat_id, frequency, message, self.max_internal_id)
        self._push_line(line)
        
        return self.max_internal_id
    
    def unregister_line(self, internal_id):
        return self._pop_line(internal_id)
    
    def save(self):
        self.files.save(self.lines)
            
    def process(self):
        res = []
        for line in self.lines.values():
            if random() < line.frequency:
                res.append(line)
        return res


# class SimpleFileSystem:
#     def __init__(self, filename):
#         self.filename = filename
#         
#     def __iter__(self):
#         lst = []
#         
#         try:
#             with open(self.filename, 'rt') as f:
#                 for line in f:
#                     lst.append(line)
#         except:
#             pass
#         
#         return iter(lst)
#     
#     def clear(self):
#         try:
#             os.remove(self.filename)
#         except:
#             pass
#         
#     def save(self):
#         pass
#     
#     def append(self, string):
#         try:
#             with open(self.filename, 'at') as f:
#                 f.write(string)
#         except:
#             pass

class DropboxFileSystem:
    def __init__(self, token, filename):
        self.box = dropbox.Dropbox(token)
        self.filename = filename
        
        try:
            if os.path.isfile(self.filename):
                os.remove(self.filename)
            self.box.files_download_to_file(self.filename, '/'+self.filename)
        except Exception as exc:
            print(exc)

    def read(self):
        lst = {}
        
        try:
            with open(self.filename, 'rb') as f:
                lst = pickle.load(f)
        except Exception as exc:
            print(exc)
            
        return lst

    def __iter__(self):
        return iter(self.read().values())

    def save(self, lines):
        try:
            dump = pickle.dumps(lines)
            self.box.files_upload(dump, '/'+self.filename, mode=dropbox.files.WriteMode.overwrite)
        except Exception as exc:
            print(exc)
