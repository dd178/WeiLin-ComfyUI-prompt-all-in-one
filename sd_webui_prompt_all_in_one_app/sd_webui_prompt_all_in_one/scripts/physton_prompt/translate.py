import json
import hashlib
import sys
import os

# 修复个别电脑环境会报的错
Path = os.path.dirname(__file__)
sys.path.append(Path)

from get_lang import get_lang
from get_translate_apis import get_translate_apis, unprotected_translate_api_config
from translator.alibaba_translator import AlibabaTranslator
from translator.amazon_translator import AmazonTranslator
from translator.baidu_translator import BaiduTranslator
from translator.deepl_translator import DeeplTranslator
from translator.google_tanslator import GoogleTranslator
from translator.microsoft_translator import MicrosoftTranslator
from translator.openai_translator import OpenaiTranslator
from translator.tencent_translator import TencentTranslator
from translator.translators_translator import TranslatorsTranslator
from translator.yandex_translator import YandexTranslator
from translator.youdao_translator import YoudaoTranslator
from translator.mymemory_translator import MyMemoryTranslator
from translator.niutrans_translator import NiutransTranslator
from translator.caiyun_translator import CaiyunTranslator
from translator.volcengine_translator import VolcengineTranslator
from translator.iflytekV1_translator import IflytekV1Translator
from translator.iflytekV2_translator import IflytekV2Translator
from translator.mbart50_translator import MBart50Translator

caches = {}


def translate(text, from_lang, to_lang, api, api_config=None, llmModel = None):
    if api_config is None:
        api_config = {}
    global caches

    def _translate_result(success, message, translated_text):
        return {
            "success": success,
            "message": message,
            "text": text,
            "translated_text": translated_text,
            "from_lang": from_lang,
            "to_lang": to_lang,
            "api": api
        }

    def _cache_name(text):
        cache_name = f'{api}.{from_lang}.{to_lang}.{text}.' + json.dumps(api_config)
        cache_name = hashlib.md5(cache_name.encode('utf-8')).hexdigest()
        return cache_name

    apis = get_translate_apis()
    find = False
    for group in apis['apis']:
        for item in group['children']:
            if item['key'] == api:
                find = item
                break
    if not find:
        return _translate_result(False, get_lang('translate_api_not_found'), '')

    try:
        texts = []
        if isinstance(text, list):
            if len(text) < 1:
                return _translate_result(False, get_lang('translate_text_is_empty'), '')
            for item in text:
                texts.append(None)
            for index in range(len(text)):
                item = text[index]
                item = item.strip()
                if item == '':
                    texts[index] = ''
                    continue
                cache_name = _cache_name(item)
                if cache_name in caches:
                    texts[index] = caches[cache_name]
                else:
                    texts[index] = None
        else:
            text = text.strip()
            if text == '':
                return _translate_result(False, get_lang('translate_text_is_empty'), '')
            cache_name = _cache_name(text)
            if cache_name in caches:
                return _translate_result(True, '', caches[cache_name])

        if api == 'google':
            translator = GoogleTranslator()
        elif api == 'microsoft':
            translator = MicrosoftTranslator()
        elif api == 'openai':
            translator = OpenaiTranslator()
        elif api == 'amazon':
            translator = AmazonTranslator()
        elif api == 'deepl':
            translator = DeeplTranslator()
        elif api == 'baidu':
            translator = BaiduTranslator()
        elif api == 'alibaba':
            translator = AlibabaTranslator()
        elif api == 'yandex':
            translator = YandexTranslator()
        elif api == 'youdao':
            translator = YoudaoTranslator()
        elif api == 'tencent':
            translator = TencentTranslator()
        elif api == 'myMemory_free' or api == 'myMemory':
            translator = MyMemoryTranslator()
        elif api == 'niutrans':
            translator = NiutransTranslator()
        elif api == 'caiyun':
            translator = CaiyunTranslator()
        elif api == 'volcengine':
            translator = VolcengineTranslator()
        elif api == 'iflytekV1':
            translator = IflytekV1Translator()
        elif api == 'iflytekV2':
            translator = IflytekV2Translator()
        elif api == 'mbart50':
            translator = MBart50Translator(llmModel)
        elif 'type' in find and find['type'] == 'translators':
            translator = TranslatorsTranslator(api)
            translator.set_translator(find['translator'])
        else:
            return _translate_result(False, get_lang('translate_api_not_support'), '')
        # print(api)

        translator.set_from_lang(from_lang)
        translator.set_to_lang(to_lang)
        translator.set_api_config(unprotected_translate_api_config('translate_api.' + api, api_config))

        if isinstance(text, list):
            translate_texts = []
            translate_indexes = []
            for index in range(len(texts)):
                item = texts[index]
                if item is None:
                    translate_indexes.append(index)
                    translate_texts.append(text[index])
            if len(translate_texts) < 1:
                return _translate_result(True, '', texts)
            result = translator.translate_batch(translate_texts)
            for index in range(len(result)):
                item = result[index]
                texts[translate_indexes[index]] = item
                caches[_cache_name(translate_texts[index])] = item
            return _translate_result(True, '', texts)
        else:
            translated_text = translator.translate(text).strip()
            caches[_cache_name(text)] = translated_text
            return _translate_result(True, '', translated_text)
    except Exception as e:
        # print(e)
        return _translate_result(False, str(e), '')
