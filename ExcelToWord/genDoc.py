# -*- coding: UTF-8 -*-
import os
import sys
import traceback

import xlrd
import win32com.client


def getCurrentPwd():
    return os.getcwd().replace('\\', '/').strip().rstrip('/')


current_pwd = getCurrentPwd()
source_file_name = getCurrentPwd() + '/数据表格.xlsx'
template_file_path = getCurrentPwd() + '/模板'
output_file_path = getCurrentPwd() + '/导出'


class WordAppHandler():
    def __init__(self):
        # ---------------
        # 打开Word，后台运行，不显示不警告
        self.wordApp = win32com.client.Dispatch('Word.Application')
        self.wordApp.Visible = 0
        self.wordApp.DisplayAlerts = 0
        # ---------------
        self.doc_fd = None  # 打开的word文档的描述符
        self.doc_filename = ''  # 打开的文件名
        self.doc_opened = False  # 是否已打开word文档

    # 实例关闭时，退出word文档和Word程序
    def __del__(self):
        self.closeDocument()
        self.wordApp.Quit()

    def openDocFile(self, file_name):
        # if self.doc_opened: return False
        if not file_name:
            print("文件名为空，打开失败！");
            return False
        self.doc_filename = file_name
        try:
            # 判断文件是否存在
            if os.path.exists(self.doc_filename):
                self.wordApp.Visible = 0
                self.wordApp.DisplayAlerts = 0
                self.doc_fd = self.wordApp.Documents.Open(self.doc_filename)
            else:
                print("文件【%s】不存在， 创建新文件" % self.doc_filename)
                self.doc_fd = self.wordApp.Documents.Add()
                # self.doc_fd.SaveAs(self.doc_filename)
            self.doc_opened = True
            print("读取文件【%s】成功" % self.doc_filename)
        except:
            print("打开文件【%s】失败：%s" % (self.doc_filename, traceback.format_exc()))
            return False
        return True

    # 替换文字，不改变样式
    def replaceContent(self, old_str, new_str):
        if not self.doc_opened:
            print("还未打开文件！")
            return False
        try:
            self.wordApp.Selection.Find.ClearFormatting()
            self.wordApp.Selection.Find.Replacement.ClearFormatting()
            self.wordApp.Selection.Find.Execute(old_str, False, False, False, False, False, True, 1, True, new_str, 2)
        except:
            print("替换内容失败【%s ==> %s】：%s" % (old_str, new_str, traceback.format_exc()))
            return False
        return True

    # 替换文字，不改变样式
    def replaceAllContent(self, d_params):
        if not self.doc_opened:
            print("还未打开文件！")
            return False
        for k, v in d_params.items():
            self.replaceContent(k, v)
        return True

    # 保存或另存为文件
    def save(self, file_name=''):
        if not self.doc_opened:
            print("还未打开文件！")
            return False
        self.wordApp.Visible = 0
        self.wordApp.DisplayAlerts = 0
        if not file_name:
            file_name = self.doc_filename
            self.doc_fd.Save()
        else:
            self.doc_fd.SaveAs(file_name)
        print("写入文件【%s】成功" % file_name)

    # 关闭word文档，不关闭Word程序
    def closeDocument(self):
        if self.doc_opened:
            self.wordApp.Documents.Close()
            self.doc_fd = None
            self.doc_filename = ''
            self.doc_opened = False


def doHandleDoc(wordApp, template_filename, output_filename, d_params):
    wordApp.openDocFile(template_filename)
    wordApp.replaceAllContent(d_params)
    wordApp.save(output_filename)
    wordApp.closeDocument()


def readSourceData():
    d_params = {}
    xls_fd = xlrd.open_workbook(source_file_name)
    sheet0 = xls_fd.sheet_by_index(0)
    row_count = sheet0.nrows
    for row in range(1, row_count):
        param = str(sheet0.cell(row, 1).value).strip()
        value = str(sheet0.cell(row, 2).value).strip()
        d_params[param] = value
    return d_params


def entrance():
    d_params = readSourceData()
    template_file_list = []
    for root, dirs, files in os.walk(template_file_path):
        for file in files:
            file_type = os.path.splitext(file)[1]
            if file_type == '.doc' or file_type == '.docx':
                template_file_list.append(file)
    if len(template_file_list) == 0: return
    wordApp = WordAppHandler()
    for file_name in template_file_list:
        template_filename = template_file_path + '/' + file_name
        output_filename = output_file_path + '/' + file_name
        doHandleDoc(wordApp, template_filename, output_filename, d_params)
    del wordApp


if __name__ == '__main__':
    args = len(sys.argv)
    file_name = ''
    if args >= 2:
        file_name = sys.argv[1]
    if file_name and not os.path.exists(file_name):
        file_name = getCurrentPwd() + '/' + file_name
        if not os.path.exists(file_name):
            file_name = source_file_name
            if not os.path.exists(file_name):
                print("数据文件不存在【%s】", file_name)
    if file_name: source_file_name = file_name

    try:
        entrance()
    except:
        print(traceback.format_exc())
