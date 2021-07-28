# -*- coding: utf-8 -*-

""" Entry point for project conversion
    @file
"""
import re
import os
import argparse
import cmake


class UVPROJXProject():
    def __init__(self, filename):
        self.filename = filename
        self.basedir = self.filename.removesuffix('\\'+os.path.basename(filename))

    def prase(self):
        try:
            with open(self.filename, 'r') as file_obj:
                self.content = str(file_obj.read())
        except FileNotFoundError:
            print("File not exisit")
        else:

            self.__include_prase()
            self.__name_prase()
            self.__chip_prase()
            self.__mems_prase()
            self.__srcs_prase()
            self.__def_prase()
            self.__startup_prase()
    def display(self):
        print('Project Name:'.join(self.name))
        print('Project chip:'.join(self.chip))
        print('Project includes: ' + ' '.join(self.include))
        print('Project defines: ' + ' '.join(self.define))
        print('Project srcs: ' + ' '.join(self.filepath))
        print('Project startup: ' + ' '.join(self.startup))
        print('Project: ' + ' '.join(self.mens))

    def __include_prase(self):
        self.include = re.findall(r"<IncludePath>(.*?)</IncludePath>", self.content)
        include_t = tuple(self.include)
        for inc in include_t:
            if not inc:
                self.include.remove(inc)
                self.include.append('.')
            else:
                self.include.remove(inc)
                self.include.extend(inc.split(';'))
        self.include = tuple(set(self.include))

    def __name_prase(self):
        self.name = re.findall(r'<TargetName>(.*?)</TargetName>', self.content)
        self.name = tuple(self.name)

    def __chip_prase(self):
        self.chip = re.findall(r'<Device>(.*?)</Device>', self.content)
        self.chip = tuple(self.chip)

    def __mems_prase(self):
        self.mens = re.findall('<Cpu>(.*?)</Cpu>', self.content)
        self.mens = tuple(self.mens)

    def __srcs_prase(self):
        srcs = re.findall(r'<Groups>[\s\S]*</Groups>', self.content)
        self.groups = re.findall('<GroupName>(.*)</GroupName>', srcs[0], re.MULTILINE)
        self.filepath = re.findall('<FilePath>(.*)</FilePath>', srcs[0], re.MULTILINE)
        self.groups = tuple(self.groups)
        self.filepath = tuple(self.filepath)

    def __def_prase(self):
        self.define = re.findall('<Define>(.*)</Define>',self.content)
        self.define = tuple(self.define[0].split(','))
    def __startup_prase(self):
        self.startup = re.findall(r'<FileName>(startup_stm32[\w]{1,10}\.s)</FileName>',self.content,re.MULTILINE)
        self.startup = tuple(self.startup)





def listdirs(path):
    def deepin(dirs,heapq):
        flag = 1
        for dir in dirs:
            if dir.is_dir():
                deepin(os.scandir(dir),heapq)
                flag = 0;
            elif flag:
                heapq.add(dirs)
    heapq = set()
    dirs = os.scandir(path)
    deepin(dirs,heapq)

    return heapq



def listfiles(path):
    def deepin(files,heapq):
        for file in files:
            if file.is_dir():
                deepin(os.scandir(file),heapq)
            else:
                heapq.append(file)
    heapq = []
    files = os.scandir(path)
    deepin(files,heapq)
    return heapq

def find_file(path, fileext):
    """ Find file with extension in path
        @param path Root path of the project
        @param fileext File extension to find
        @return File name
    """

    files = listfiles(path)
    files = tuple(files)
    for file in files:
        if file.name.endswith(fileext):
            return file.path
    raise FileNotFoundError

def find_gcc_startup(path,startup):
    files = listfiles(path)
    files = tuple(files)
    for file in files:
        temp = re.findall(r'Drivers[\\/]{1,2}CMSIS[\\/]{1,2}Device[\\/]{1,2}ST[\\/]{1,2}[\s\S]+',file.path)
        gcc = re.findall(startup,file.path,re.IGNORECASE)
        if gcc and temp and 'gcc' in file.path:
            return file.path
    print('fail to find the startup file to gcc')
    return None

if __name__ == '__main__':
    """ Parses params and calls the right conversion"""

    parser = argparse.ArgumentParser()
    # parser.add_argument("format", choices=("ewp", "uvprojx"))
    parser.add_argument("path", type=str, help="Root directory of project")
	#"--ewp", help="Search for *.EWP file in project structure", action='store_true')
    #parser.add_argument("--uvprojx", help="Search for *.UPROJX file in project structure", action='store_true')
    args = parser.parse_args()

    if os.path.isdir(args.path):
        if args.path.endswith('\\'):
            args.path = args.path[:-1:]
        print('Looking for *.uvprojx file in ' + args.path)
        filename = find_file(args.path, '.uvprojx')
        print(f"file is {filename}")
        if filename is not None:
            print('Found project file: ' + filename)
            project = UVPROJXProject(filename)
            project.prase()
            project.display()
            project.path = args.path
            project.gcc = find_gcc_startup(args.path,project.startup[0])
            print(f"GCC startup file is {project.gcc}")

            cmakefile = cmake.CMake(project)
            cmakefile.populateCMake()
            print('suceess generate')
        else:
            print('No project *.uvprojx file found')

    else:
        print('Not a valid file path')
