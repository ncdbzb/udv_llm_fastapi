import logging

doc_info = logging.getLogger('upload_doc_info')
doc_info.setLevel(logging.DEBUG)

console_handler_info = logging.StreamHandler()
console_handler_info.setLevel(logging.DEBUG)

formatter_info = logging.Formatter('%(levelname)s: %(message)s')
console_handler_info.setFormatter(formatter_info)

doc_info.addHandler(console_handler_info)
