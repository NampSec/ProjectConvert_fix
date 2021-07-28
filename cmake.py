# -*- coding: utf-8 -*-

""" CMake generation module
    @file
"""
import re
import os
import platform
import datetime
from jinja2 import Environment, FileSystemLoader

class CMake (object):
    
    def __init__(self, project):
        
        self.project = project
        self.context = {}
        
    def populateCMake (self):
        """ Generate CMakeList.txt file for building the project
        """

        # For debug run cmake -DCMAKE_BUILD_TYPE=Debug or Release
        cmake = {}
        #fpu = '-mfpu=fpv5-sp-d16 -mfloat-abi=softfp'
        fpu = ''
        
        core = ''
        self.index = os.path.abspath('.')
        os.chdir(self.project.basedir)

        if 'STM32F0' in self.project.chip[0]:
            core = '-mcpu=cortex-m0'
        elif 'STM32F1' in self.project.chip[0]:
            core = '-mcpu=cortex-m3'
        elif 'STM32F2' in self.project.chip[0]:
            core = '-mcpu=cortex-m3'
        elif 'STM32F3' in self.project.chip[0]:
            core = '-mcpu=cortex-m4'
        elif 'STM32F4' in self.project.chip[0]:
            core = '-mcpu=cortex-m4'
        elif 'STM32F7' in self.project.chip[0]:
            core = '-mcpu=cortex-m7'
        elif 'STM32L0' in self.project.chip[0]:
            core = '-mcpu=cortex-m0plus'
        elif 'STM32L1' in self.project.chip[0]:
            core = '-mcpu=cortex-m3'
        elif 'STM32L4' in self.project.chip[0]:
            core = '-mcpu=cortex-m4'

        cmake['version'] = '3.1'
        cmake['project'] = self.project.name[0]
        cmake['incs'] = []
        for inc in self.project.include:
            cmake['incs'].append(os.path.abspath(inc.replace('\\','/')).replace('\\','//'))

        cmake['srcs'] = []

        i=0
                
        cmake['files']=[]
        cmake['ass']=[]
        
        for file in self.project.filepath:
            if file.endswith('.c') or file.endswith('.h') or file.endswith('.cpp') or file.endswith('.s'):
                cmake['files'].append({'path': os.path.abspath(file.replace('\\','/')).replace('\\','//'),'var':'SRC_FILE' + str(i)})
                i = i+1
#add stm32fxx.s
        if self.project.gcc:
            print (f'Assembly added {self.project.gcc}' )
            cmake['ass'].append({'path': os.path.abspath(self.project.gcc.replace('\\','/')).replace('\\','//')})

        cmake['cxx'] = 'false'
        
        cmake['c_flags'] = '-g -Wextra -Wshadow -Wimplicit-function-declaration -Wredundant-decls -Wmissing-prototypes -Wstrict-prototypes -fno-common -ffunction-sections -fdata-sections -MD -Wall -Wundef -mthumb ' + core + ' ' + fpu

        cmake['cxx_flags'] = '-Wextra -Wshadow -Wredundant-decls  -Weffc++ -fno-common -ffunction-sections -fdata-sections -MD -Wall -Wundef -mthumb ' + core + ' ' + fpu
 
        cmake['asm_flags'] = '-g -mthumb ' + core + ' ' + fpu #+ ' -x assembler-with-cpp'
        cmake['linker_flags'] = '-g -Wl,--gc-sections -Wl,-Map=' + cmake['project'] + '.map -mthumb ' + core + ' ' + fpu
        cmake['linker_script'] = 'STM32FLASH.ld'
        cmake['linker_path'] = ''
        os.chdir(self.index)
   
        self.linkerScript('STM32FLASH.ld',os.path.join(self.project.path,'STM32FLASH.ld'))
        
        cmake['oocd_target'] = self.project.chip[0]
        cmake['defines'] = list(self.project.define)

            
        cmake['libs'] = []
        
        self.context['cmake'] = cmake
        
        abspath = os.path.abspath(os.path.join(self.project.path,'CMakeLists.txt'))
        self.generateFile('CMakeLists.txt', abspath)

        print ('Created file CMakeLists.txt [{}]'.format(abspath))
        
#    def generateFile (self, pathSrc, pathDst='', author='Pegasus', version='v1.0.0', licence='licence.txt', template_dir='../PegasusTemplates'):
    def generateFile (self, pathSrc, pathDst='', author='Pegasus', version='v1.0.0', licence='licence.txt', template_dir='.'):
        
        if (pathDst == ''):
            pathDst = pathSrc
            
        self.context['file'] = os.path.basename(str(pathSrc))
        self.context['author'] = author
        self.context['date'] = datetime.date.today().strftime('%d, %b %Y')
        self.context['version'] = version
        self.context['licence'] = licence
        
        env = Environment(loader=FileSystemLoader(template_dir),trim_blocks=True,lstrip_blocks=True)
        template = env.get_template(str(pathSrc))
        
        generated_code = template.render(self.context)
            
        if platform.system() == 'Windows':    

            with open(pathDst, 'w') as f:
                f.write(generated_code)
        
        elif platform.system() == 'Linux':

            with open(pathDst, 'w') as f:
                f.write(generated_code)        
        else:
            # Different OS than Windows or Linux            
            pass
    
    def linkerScript(self,pathSrc, pathDst='',template_dir='.'):
#    def linkerScript(self,pathSrc, pathDst='',template_dir='.../PegasusTemplates'):
                
        if (pathDst == ''):
            pathDst = pathSrc
            
        self.context['file'] = os.path.basename(str(pathSrc))
        romsize = re.findall(r'IROM\((.*?)\)',self.project.mens[0])
        ramsize = re.findall(r'IRAM\((.*?)\)',self.project.mens[0])
        if '-' in romsize:
             romsizes = eval(romsize[0])
             ramsizes = eval(ramsize[0])
        else:
            print('your are using KEIL V5')
            romsizes = int((re.findall(r'\,(.*)',romsize[0]))[0],base=16)
            ramsizes = int((re.findall(r'\,(.*)',ramsize[0]))[0],base=16)

        self.context['flash'] = round(abs(romsizes) / 1024)
        self.context['ram'] = round(abs(ramsizes) / 1024)
        env = Environment(loader=FileSystemLoader(template_dir),trim_blocks=True,lstrip_blocks=True)
        template = env.get_template(str(pathSrc))
        
        generated_code = template.render(self.context)
            
        if platform.system() == 'Windows':    

            with open(pathDst, 'w') as f:
                f.write(generated_code)
        
        elif platform.system() == 'Linux':

            with open(pathDst, 'w') as f:
                f.write(generated_code)        
        else:
            # Different OS than Windows or Linux            
            pass

