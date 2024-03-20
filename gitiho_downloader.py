import sys
from PyQt6.QtWidgets import QHBoxLayout, QMessageBox, QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel, QTextEdit, QStackedLayout
import os
import requests
from bs4 import BeautifulSoup
import logging
import shutil
import m3u8_To_MP4
import re
home_directory = os.getcwd() + '\\Courses\\'

if not os.path.exists(home_directory):
    try:
        os.makedirs(home_directory)
        print(f"Folder '{home_directory}' created!")
    except:
        print(f"Folder '{home_directory}' can't create!")
else:
    print(f"Folder '{home_directory}' exists!")

session = requests.Session()
headers = {}


class DownloadApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Ứng dụng Download khóa học")
        self.setup_ui()

    def setup_ui(self):
        mainLayout = QVBoxLayout(self)

        self.loginWidget = QWidget(self)
        loginLayout = QVBoxLayout(self.loginWidget)
        self.usernameEdit = QLineEdit(self.loginWidget)
        self.usernameEdit.setText('bichthuy@tranghuylogistics.com')
        self.passwordEdit = QLineEdit(self.loginWidget)
        self.passwordEdit.setEchoMode(QLineEdit.EchoMode.Password)
        self.passwordEdit.setText("123456x")
        self.loginButton = QPushButton("Đăng nhập", self.loginWidget)

        self.loginButton.clicked.connect(self.login)

        loginLayout.addWidget(self.usernameEdit)
        loginLayout.addWidget(self.passwordEdit)
        loginLayout.addWidget(self.loginButton)

        self.layout2Widget = QWidget(self)
        layout2 = QVBoxLayout(self.layout2Widget)
        self.loggedInLabel = QLabel("Đăng nhập thành công!", self.layout2Widget)
        downloadLayout = QHBoxLayout()
        self.downloadAllEdit = QLineEdit(self.layout2Widget)
        self.downloadAllEdit.setText("0")
        self.downloadAllButton = QPushButton("Download All", self.layout2Widget)
        downloadLayout.addWidget(self.downloadAllEdit)
        downloadLayout.addWidget(self.downloadAllButton)

        self.downloadUrlButton = QPushButton("Download from URL", self.layout2Widget)
        self.urlTextEdit = QLineEdit(self.layout2Widget)

        layout2.addWidget(self.loggedInLabel)
        layout2.addLayout(downloadLayout)
        layout2.addWidget(self.downloadUrlButton)
        layout2.addWidget(self.urlTextEdit)

        self.stackedLayout = QStackedLayout()
        self.stackedLayout.addWidget(self.loginWidget)
        self.stackedLayout.addWidget(self.layout2Widget)

        self.downloadAllButton.clicked.connect(self.confirm_download_all)
        self.downloadUrlButton.clicked.connect(self.confirm_download_from_url)

        mainLayout.addLayout(self.stackedLayout)

    def login(self):
        global headers
        print("[=] Logging....")
        data = {
            "email": self.usernameEdit.text().strip(),
            "password": self.passwordEdit.text().strip()
        }
        response = session.post('https://tranghuy.gitiho.com/auth/login', data=data)

        cookies = response.cookies
        csrf_token = self.get_csrf_token(response.text)
        headers = {'Cookie': f"XSRF-TOKEN={cookies['XSRF-TOKEN']}; gitiho={cookies['gitiho']}",
                   'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) Gecko/20100101 Firefox/123.0',
                   'Accept-Language': 'en-US,en;q=0.5',
                   'Accept-Encoding': 'gzip, deflate, br',
                   'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                   'X-Requested-With': 'XMLHttpRequest',
                   'X-Csrf-Token': csrf_token
                   }
        response = session.post('https://tranghuy.gitiho.com/auth/login', headers=headers, data=data)
        if "Success" in response.text:
            self.stackedLayout.setCurrentIndex(1)
            print("[+] Logged!")
        else:
            QMessageBox.warning(self, "Lỗi", "Tên người dùng hoặc mật khẩu không chính xác!")
            print("[-] Logging failed!")

    def get_csrf_token(self, text):
        soup = BeautifulSoup(text, 'html.parser')
        csrf_token = soup.find('meta', {'name': '_token'})['content']
        return csrf_token

    def get_url(self, url):
        html_content = session.get(url).text
        pattern = r'"source":"(https?://[^"]+\.m3u8)"'

        # Tìm kiếm và trích xuất URL m3u8 từ đoạn mã JavaScript
        matches = re.findall(pattern, html_content.replace('\/','/'))

        # Hiển thị kết quả
        if matches:
            return matches[0]
            # print("URL m3u8:", matches[0])
        else:
            print("Không tìm thấy URL m3u8 trong đoạn mã JavaScript.")
            return None
            

    def list_courses(self):
        print("[=] Getting All Courses.")
        url_course = []
        page = 1
        response = session.get(f"https://tranghuy.gitiho.com/my-learning?page={page}").text
        while len(response) > 650000:
            soup = BeautifulSoup(response, 'html.parser')
            all_a_tags = soup.find_all("a")
            for a_tag in all_a_tags:
                img_tag = a_tag.find("img")
                if img_tag:
                    alt_text = img_tag.get("alt")
                    href = a_tag.get("href")
                    course_info = {'url': href, 'alt_text': alt_text}
                    url_course.append(course_info)
            page += 1
            response = session.get(f"https://tranghuy.gitiho.com/my-learning?page={page}").text
        url_course = [url for url in url_course if 'studying' in url['url']]
        print("[+] Getted all courses!")
        return url_course

    def list_directory(self, url_course):
        print("[=] Getting tree!")
        html_content = session.get(url_course).text
        soup = BeautifulSoup(html_content, 'html.parser')
        sections = soup.find_all('div', class_='list-section')
        analysis_result = []
        for section in sections:
            chapter_title_element = section.find('span', class_='fw-700')
            chapter_duration_element = section.find('span', class_='section-info')
            if chapter_title_element and chapter_duration_element:
                chapter_title = chapter_title_element.parent.text.strip().replace('\t', '').replace('\n', ' ')
                chapter_duration = chapter_duration_element.text.strip().replace('\t', '').replace('\n', '')
                items = section.find_all('li')
                chapter_items = []
                for item in items:
                    item_title = item.find('span', class_='content-title').text.strip().replace('\t', '').replace(
                        '\n', '')
                    item_link = item['data-href']
                    item_duration = item.find('span', class_='duration').text.strip().replace('\t', '').replace('\n',
                                                                                                                   '')
                    chapter_items.append({'title': item_title, 'link': item_link, 'duration': item_duration})
                analysis_result.append({'chapter_title': chapter_title, 'duration': chapter_duration,
                                        'items': chapter_items})
        print("[+] Getted tree!")
        return analysis_result

    def downloader(self, url, directory, file):
        try:
            m3u8_To_MP4.multithread_download(url, mp4_file_dir=directory, mp4_file_name=file)
        except Exception as e:
            print(e)

    def create_directory(self, base, directory_path):
        if not os.path.exists(base + directory_path):
            try:
                print(base + directory_path)
                os.makedirs(base + directory_path)
                print(f"Folder '{base + directory_path}' created!")
                return True
            except Exception as e:
                print(2)
                print(e)
                print(f"Folder '{base + directory_path}' can't create!")
                return False
        else:
            reply = QMessageBox.question(self, "Xác nhận", f"Folder '{base + directory_path}' exists! -> Delete Folder!",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    shutil.rmtree(base + directory_path)
                    os.makedirs(base + directory_path)
                except Exception as e:
                    print(3)
                    print(e)
                    QMessageBox.warning(self, "Lỗi", "Không thể thực hiện!")
                return True
            else:
                print(f"Folder '{base + directory_path}' exists!")
            return False

    def get_name_course(self, url):
        html_content = session.get(url).text
        soup = BeautifulSoup(html_content, 'html.parser')
        d_flex_div = soup.find('div', class_='d-flex mr-3')
        if d_flex_div:
            strong_tag = d_flex_div.find('strong')
            if strong_tag:
                strong_text = strong_tag.text.strip()
                return strong_text
        return None

    def download_with_course(self, url):
        name_course = self.get_name_course(url)
        base = home_directory + name_course + '\\'
        directories = self.list_directory(url)
        for directory in (directories):
            if self.create_directory(base, directory['chapter_title'].replace(":", '')) is True:
                path = base + directory['chapter_title'].replace(":", '')
                try:
                    [self.downloader(self.get_url(video['link']), path, video['title'].replace('/', '-')) for video in
                     directory['items'] if self.get_url(video['link']) is not None]
                except Exception as e:
                    print(6)
                    print(e)

    def confirm_download_all(self):
        reply = QMessageBox.question(self, "Xác nhận", "Bạn có muốn tải xuống tất cả không?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            print("Downloading all...")
            courses = self.list_courses()
            try:
                start = self.downloadAllEdit.text().strip().split('-')
                if len(start>1):
                    end = int(start[1])
                else: 
                    end =len(courses)
                for inx in range(start, end):
                    self.download_with_course(courses[inx]['url'].strip())
            except Exception as e:
                print(4)
                print(e)

        else:
            print("Cancelled download all")

    def confirm_download_from_url(self):
        reply = QMessageBox.question(self, "Xác nhận", "Bạn có muốn tải từ URL không?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.download_with_course(self.urlTextEdit.text().strip())
            except Exception as e:
                print(5)
                print(e)
                QMessageBox.warning(self, "Lỗi", "Không thể download từ url này!")

        else:
            print("Cancelled download from URL")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DownloadApp()
    window.show()
    sys.exit(app.exec())
