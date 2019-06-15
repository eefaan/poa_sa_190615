from bs4 import BeautifulSoup
import requests
import re
import traceback
import time
import json

url_index = 'http://mobile.zol.com.cn/manu_613.shtml'
url_list = 'http://detail.zol.com.cn/cell_phone_index/subcate57_613_list_1_0_1_2_0_{0}.html'
url_revi = 'http://detail.zol.com.cn/1/1224162/review.shtml'
url_arti = 'http://detail.zol.com.cn/1/{0}/article.shtml'
url_info = 'http://detail.zol.com.cn/xhr4_Review_GetList_proId={0}%5Elevel=0%5Efilter=1%5Epage={1}.html'

kv = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.12 Safari/537.36'}
# kv = {'User-Agent':'Mozilla/5.0'}

filename_comment = "./zgcComment.txt"
filename_evaluation = "./zgcEva.txt"

debug = False

def main():
	clist = []
	# get Cp list
	getCpList(clist)
	print('CommentCrawler begin.')
	userCommentCrawler(clist)
	print('CommentCrawler done.')
	print('EvaluationCrawler begin.')
	evaluationCrawler(clist)
	print('EvaluationCrawler done.')

def getCpList(clist):
	for i in range(1, 13):
		parse_getCpList(clist, url_list.format(i))

def parse_getCpList(clist, url):
	try:
		# get the raw page
		print(url)
		response = requests.get(url, headers = kv)
		response.raise_for_status()
		response.encoding=response.apparent_encoding
		# construct with bs4
		soup = BeautifulSoup(response.text, 'html.parser')
		# find the tag 'a' and match cellphone's id
		a = soup.find_all('a')
		for i in a:
			try:
				href = i.attrs['href']
				matchObj = re.search(r'index([\d]*).shtml', href) 
				if matchObj:
					clist.append(matchObj.group(1))
			except:
				continue
	except:
		print('scrape list error.')
		return ""

def userCommentCrawler(clist):	
	# flash the file with localtime
	with open(filename_comment, 'w+')as f:
		f.write(time.asctime(time.localtime(time.time())) + '\n')
	for i in clist:
		getComInfo(url_revi.format(i), i, filename_comment)

def getComInfo(url_head, good_id, filename):
	with open(filename, 'a+', encoding='utf-8')as f:
		result = {}
		head = ''
		try:
			f.write('\n')
			# get the raw page_head
			response = requests.get(url_head, headers = kv)
			response.raise_for_status()
			response.encoding = response.apparent_encoding
			soup = BeautifulSoup(response.text, 'html.parser')
			# get name of the cellphone
			h1 = soup.find_all('h1')
			if debug: print(h1[0].string[:-2] + '\n')
			head = h1[0].string[:-2]
			result[h1[0].string[:-2]] = []
			# f.write(h1[0].string[:-2] + '\n')
		except:
			print('crawl cellphone\'s name error, url: ' + url_head)
			return

		# get the raw page_comment
		for page_index in range(1, 100):
			try:
				response = requests.get(url_info.format(good_id, page_index), headers = kv)
				response.raise_for_status()
				response.encoding = response.apparent_encoding
				# trans ajax to json
				d = response.json()
				# trans json to html
				html_text = d['list']
				# construct with bs4
				soup = BeautifulSoup(html_text, 'html.parser')

				# judge the last page of comment
				if soup.find('div', {'class': 'empty-comment'}):
					break

				div = soup.find_all('div', {'class': 'comment-list-content'})
				for i in div:
					comment_dict = {}
					# print(type(i))
					# print(i)
					if debug: print()
					# f.write('\n')

					# store good, bad, summary/summary_2
					div_details = i.find_all('div', {'class': 'words'})
					for j in div_details:
						if j.find('strong', {'class': 'good'}):
							if debug: print('good:', j.find('p').string)
							# f.write('good: ' + j.find('p').string + '\n')
							comment_dict['good'] = j.find('p').string
						elif j.find('strong', {'class': 'bad'}):
							if debug: print('bad:', j.find('p').string)
							# f.write('bad: ' + j.find('p').string + '\n')
							comment_dict['bad'] = j.find('p').string
						elif j.find('strong', {'class': 'summary'}):
							if debug: print('summary:', j.find('p').string)
							# f.write('summary: ' + j.find('p').string + '\n')
							comment_dict['summary'] = j.find('p').string
					if i.find('div', {'class': 'words-article'}):
						div_details_2 = i.find('div', {'class': 'words-article'})
						if debug: print('summary_2:', div_details_2.find('p').string)
						# f.write('summary: ' + div_details_2.find('p').string + '\n')
					else:
						pass

					# if 展开全文 con
					div_more_hide = i.find('div', {'class': 'view-more hide'})
					if div_more_hide is not None:
						# update the comment list
						if len(comment_dict)>0: result[head].append(comment_dict)
						continue

					# else 查看全文
					div_more = i.find('div', {'class': 'view-more'})
					if div_more is not None:
						ftext_tag = div_more.find('a')
						ftext_url = ftext_tag.attrs['href']
						if debug: print('more:', ftext_url)
						# crawl the full text
						# f.write('summary: ')
						response_more = requests.get(ftext_url, headers = kv)
						response_more.raise_for_status()
						response_more.encoding = response_more.apparent_encoding
						soup_more = BeautifulSoup(response_more.text, 'html.parser')
						content = soup_more.find('div', {'class': 'article-content single-article-content'})
						p_all = content.find_all('p', {'class': False})
						comment_dict['summary'] = ''
						for p in p_all:
							# filter the <br> tag
							if debug: print(p.find(text=True))
							# f.write(p.find(text=True) + '\n')
							comment_dict['summary'] += p.find(text=True) + '\n'
					# update the comment list
					if len(comment_dict)>0: result[head].append(comment_dict)
			except:
				print('error when crawl comment, url: ' + url_info.format(good_id, page_index))
		# write back to file
		f.write(json.dumps(result, sort_keys=True, indent=4, ensure_ascii=False) + '\n')
	return


def evaluationCrawler(clist):
	# flash the file with localtime
	with open(filename_evaluation, 'w+')as f:
		f.write(time.asctime(time.localtime(time.time())) + '\n')
	for i in clist:
		getEvaInfo(url_arti.format(i), filename_evaluation)

def getEvaInfo(url, filename):
	with open(filename, 'a+', encoding='utf-8')as f:
		result = {}
		head = ''
		try:
			f.write('\n')
			# get the raw page_head
			response = requests.get(url, headers = kv)
			response.raise_for_status()
			response.encoding = response.apparent_encoding
			soup = BeautifulSoup(response.text, 'html.parser')
			# get name of the cellphone
			h1 = soup.find_all('h1')
			if debug: print(h1[0].string[:-4] + '\n')
			head = h1[0].string[:-4]
			result[head] = []
			# f.write(h1[0].string[:-2] + '\n')
		except:
			print('crawl cellphone\'s name error, url: ' + url)
			return

		try:
			r = requests.get(url, headers = kv)
			soup = BeautifulSoup(r.text, 'html.parser')
			li = soup.find_all('li', {'class': 'clearfix', 'data-page': True})
			for i in li:
				eva_dict = {}
				a = i.find('a', {'href': True})
				
				url = a.attrs['href']
				if debug: print(url)
				if debug: print(url[:-5]+'_all.html')
				temp_url = url[:-5]+'_all.html'
				if re.search(r'bbs', url):
					if debug: print('pass')
					continue
				if re.search(r'slide', url):
					if debug: print('pass')
					continue
				# obj = re.search(r'\/([0-9]+)\.html', url)
				# print(obj.group(1))

				# get raw page
				r_s = requests.get(temp_url, headers = kv)
				soup = BeautifulSoup(r_s.text, 'html.parser')
				# get head
				h1 = soup.find('h1')
				if debug: print(h1.string)

				# judge if 404
				if re.search(r'您访问的页面已被删除', h1.string):
					print('error when crawl Eva, url(404): ' + url)
					continue

				# f.write('head: ' + h1.string + '\n')
				eva_dict['title'] = h1.string
				# get content
				# f.write('content: ')
				eva_dict['content'] = ''

				cont = soup.find('div', {'class': 'article-cont article-all-cont clearfix'})
				p_all = cont.find_all('p', {'text-align': False})
				for p in p_all:
					attrs_dict = p.attrs
					if attrs_dict.__contains__('style'):
						if re.search(r'text-align', attrs_dict['style']):
							continue
					text = p.find_all(text=True)
					for word in text:
						if word:
							if debug: print(word, end = '')
							# f.write(word)
							eva_dict['content'] += word
					if debug :print()
					# f.write('\n')
					eva_dict['content'] += '\n'

				# end of reading a page
				# f.write('\n')
				if len(eva_dict)>0: result[head].append(eva_dict)
			# write back to file
			f.write(json.dumps(result, sort_keys=True, indent=4, ensure_ascii=False) + '\n')
		except:
			print('error when crawl Eva, url: ' + url)
			return

if __name__ == '__main__':
	main()
