import requests

# 以下代码仅仅是一个学习使用的简单爬虫。使用爬虫获取谷歌翻译的准确结果不太现实，因为谷歌经常修改自己的调用接口
# 如果非常追求翻译的准确程序可以考虑申请谷歌翻译的api或者使用selenium的方式获取翻译结果
class TranslateByGoogle():

    # 初始化信息
    def __init__(self):
    # 参数“x-goog-batchexecute-bgr” 在翻译不同的句子会发生变化，故无法保证最后翻译结果的准确度
    # 以下代码“x-goog-batchexecute-bgr” 的参数使用在翻译“他静静的坐在床边弹琴”
        self.__headers = {
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36",
            "x-goog-batchexecute-bgr":"""[";QF64XhPQAAbGaIJMxmhfS_ZerNaM8YMmACkAIwj8RnBjsrnR8n_IWQuEKz8j4fiNoHCOKHfUCp4ZYIn0qaqQyaWhax8AAADmTwAAAAx1AQcXAQ2wpqc15XYbdjg3dVGZaTob7bpcvUfO7rZikTRF9DR2vJ-oq4FiXp3hemZQpyaLqulBPffZOLcyf-MmUpsvmMaP5mn9gZYKOwC0wgftat8yiVkxJ_b202x0DwYV3YLHxQZb6ullf0gAk-Q0RZysDCLPX2r9bdgO72VN01uQw6rm59jXAwB0fwbfmoOeY77OVxfTgYKPlAD8u6tKlgB53M2ZzBG_tbJ-FrRkLp6Q9iNVyWjqg42pr2loteoR51oCcjVGSzAHju29uTGW0uyMt99w8L6HxhUpTqsHcW-A0Uw9j_BoQAuqUo7yB0UUNf46Wm6WdnLEkvwbaq4T8WOynzbxbGDMkhcS63aKZB2c-YQCVo3Y-RqlIhjyShH44Y2Xiv5w3Y5_a4mOWzosqIPHOOwhCJH1JqA9tEn6gECDh3h_4LdtJoDzAd7gs6qqEmGvkEzAxF8RVzBm_2e6dtaAA3GwRJ8s_WGwy7miFTNOl5_9iItTslNn7FJAMpmhwiNIRJsC7GNi_emeQOf1uOkck5d2mU_p-axg-0COpzL_GgW__XtRC0SJ8Rvx1UsFTiNbIl8upsDRVtOmBc8YPki-vTdO0fj8Zzr8s-mH3sPiuvFnAlPXSwbp-O30FYv5408LSy3KftCMAfZtXhb1JZY6GHkyM7_KzdY_09A08nunsIbGA8fQ4TJItXyRUVkhe6xLBvDUC5ErEON1799COgplnpLFgLQQCq9lARRHuW2nLsmU4aq0d-lav_s2EdWv02Bo1OpKpfI49Om9xBA5xvFt3dbU06A1bx0yzhfNd2uIG89pZ4OKoNBg6juo_lBx0DtUOYnf-POcmHQCCZvRYtWDxXdAZvk-GKZhed8OYxk_5xIrupo6clLXuvIngMe3AQ2J1URQW59j7znthip8H5u3YNSmuf41Sty4L6E9b3B7--Z5ZSuBGvKEuzDea2QmEdCNcBwfEWFg99MdNcOkyqsbPWVgZQdV3gU0cdCr1E3ou-Tb3J8QP4DiL4x-PkCeo057pXw594fU00jyQYqplL2wHIV6VTtkcei0bKvqvJp7NNJ4NJC7g749w0cruebAhot7IobX-3VkLhQWudpaZhDPeZW0v9PNKVfHIeXBeeGaewd59pDIjaxVMPwpV16Y2pXnGbAJKDgkN4o",null,null,525,36,null,null,0,"2"]"""}

        self.__post_url = "https://translate.google.cn/_/TranslateWebserverUi/data/batchexecute"
        self.__data = {
            "rpcids": "MkEWBc",
            "f.sid": "6951160582206934436",
            "bl": "boq_translate-webserver_20210823.08_p0",
            "hl": "zh-CN",
            "soc-app": "1",
            "soc-platform": "1",
            "soc-device": "1",
            "_reqid": "3379651",
            "rt": "c"
        }

    # 发送post请求，返回翻译结果
    def translate(self, key_words, language_to="en", language_from = "auto"):
        """
        :param key_words: 翻译关键字
        :param language_to: 翻译为?，默认为英语
        :param language_from: 输入语言，默认自动识别
        """
        n = 12
        if language_to in ("en", "de"):
            n = 10
        self.__data["f.req"] = '[[["MkEWBc","[[\\"{}\\",\\"{}\\",\\"{}\\",true],[null]]",null,"generic"]]]'.format(key_words, language_from, language_to )
        r = requests.post(self.__post_url, data=self.__data, headers=self.__headers)
        response = r.content.decode().split('\"')[n]
        return response[:-1]
    
if __name__ == "__main__":
    """
        de：德语
        ja：日语
        sv：瑞典语
        nl：荷兰语
        ar：阿拉伯语
        ko：韩语
        pt：葡萄牙语
        zh-CN：中文简体
    """
    str1 = "人生苦短，我用Python."
    tran = TranslateByGoogle()
    print("英语： {}".format(tran.translate(str1)))
    print("德语： {}".format(tran.translate(str1, "de")))
    print("日语： {}".format(tran.translate(str1, "ja")))
    print("蒙语： {}".format(tran.translate(str1, "mn")))
    
    str2 = "Life is short, I use python"
    print("中文： {}".format(tran.translate(str2, "zh-CN")))

