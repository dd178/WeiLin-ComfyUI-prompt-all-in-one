import gradio as gr
import os
import sys
from pathlib import Path

from server import PromptServer
from aiohttp import web

# 修复个别电脑环境会报的错
Path = os.path.dirname(__file__)
sys.path.append(Path)
# 添加环境再导入包
from physton_prompt.storage import Storage
from physton_prompt.get_extensions import get_extensions
from physton_prompt.get_token_counter import get_token_counter
from physton_prompt.get_i18n import get_i18n
from physton_prompt.get_translate_apis import get_translate_apis, privacy_translate_api_config, unprotected_translate_api_config
from physton_prompt.translate import translate
from physton_prompt.history import History
from physton_prompt.csv import get_csvs, get_csv
from physton_prompt.styles import get_style_full_path, get_extension_css_list
from physton_prompt.get_extra_networks import get_extra_networks
from physton_prompt.packages import get_packages_state, install_package, get_llm_packages_state,install_llm_package
from physton_prompt.gen_openai import gen_openai
from physton_prompt.get_lang import get_lang
from physton_prompt.get_version import get_git_commit_version, get_git_remote_versions, get_latest_version
from physton_prompt.mbart50 import Translator as mbart50_translator
from physton_prompt.get_group_tags import get_group_tags
from physton_prompt.get_group_tags import addGroupTag
from physton_prompt.get_group_tags import editGroupTag
from physton_prompt.get_group_tags import deleteGroupTag
from physton_prompt.get_group_tags import addNewNodeGroup
from physton_prompt.get_group_tags import addNewGroup
from physton_prompt.get_group_tags import editNodeGroup
from physton_prompt.get_group_tags import editChildNodeGroup
from physton_prompt.get_group_tags import deleteNodeGroup
from physton_prompt.get_group_tags import deleteChildNodeGroup

try:
    from ...modules.shared import cmd_opts

    if cmd_opts.data_dir:
        extension_dir = os.path.join(os.path.dirname(__file__),'../')
        extension_dir = os.path.normpath(extension_dir) + os.path.sep
        data_dir = os.path.normpath(cmd_opts.data_dir) + os.path.sep
        webui_dir = os.path.normpath(Path().absolute()) + os.path.sep
        if not extension_dir.startswith(webui_dir):
            find = False
            if cmd_opts.gradio_allowed_path:
                for path in cmd_opts.gradio_allowed_path:
                    path = os.path.normpath(path) + os.path.sep
                    if path == extension_dir:
                        find = path
                        break
                    elif extension_dir.startswith(path):
                        find = path
                        break
                    else:
                        pass
            if not find:
                message = f'''
\033[1;31m[sd-webui-prompt-all-in-one]
As you have set the --data-dir parameter and have not added the extension path to the --gradio-allowed-path parameter, the extension may not function properly. Please add the following startup parameter:
由于你设置了 --data-dir 参数，并且没有将本扩展路径加入到 --gradio-allowed-path 参数中，所以本扩展可能无法正常运行。请添加启动参数：
\033[1;32m--gradio-allowed-path="{extension_dir}"
\033[0m
                '''
                print(message)
except Exception as e:
    pass


def on_app_started(_: gr.Blocks):
    st = Storage()
    hi = History()
    localLLMTransaltor=None

    @PromptServer.instance.routes.get("/weilin/physton_prompt/get_version")
    async def _get_version(request):
        return web.json_response({
            'version': get_git_commit_version(),
            'latest_version': get_latest_version(),
        })

    @PromptServer.instance.routes.get("/weilin/physton_prompt/get_remote_versions")
    async def _get_remote_versions(request):
        page  = int(request.query.get('page'))
        per_page = int(request.query.get('per_page'))
        if page < 1:
            page = 1
        if per_page < 100:
            per_page = 100
        return web.json_response({
            'versions': get_git_remote_versions(page, per_page),
        })

    @PromptServer.instance.routes.get("/weilin/physton_prompt/get_config")
    async def _get_config(request):
        return web.json_response({
            'i18n': get_i18n(True),
            'translate_apis': get_translate_apis(True),
            'packages_state': get_packages_state(),
            'python': sys.executable,
        })
    
    # 新增LLM
    @PromptServer.instance.routes.get("/weilin/physton_prompt/get_llm_config")
    async def _get_config(request):
        return web.json_response({
            'packages_state': get_llm_packages_state(),
            'python': sys.executable,
        })

    @PromptServer.instance.routes.post("/weilin/physton_prompt/install_llm_package")
    async def _install_llm_package(request):
        try:
            data = await request.json()
        except:
            data = {}
        if 'name' not in data:
            return web.json_response({"result": get_lang('is_required', {'0': 'name'})})
        if 'package' not in data:
            return web.json_response({"result": get_lang('is_required', {'0': 'package'})})
        return web.json_response({"result": install_llm_package(data['name'], data['package'])})
    
    @PromptServer.instance.routes.post("/weilin/physton_prompt/install_package")
    async def _install_package(request):
        try:
            data = await request.json()
        except:
            data = {}
        if 'name' not in data:
            return web.json_response({"result": get_lang('is_required', {'0': 'name'})})
        if 'package' not in data:
            return web.json_response({"result": get_lang('is_required', {'0': 'package'})})
        return web.json_response({"result": install_package(data['name'], data['package'])})

    @PromptServer.instance.routes.get("/weilin/physton_prompt/get_extensions")
    async def _get_extensions(request):
        return web.json_response({"extends": get_extensions()})

    @PromptServer.instance.routes.post("/weilin/physton_prompt/token_counter")
    async def _token_counter(request):
        data = await request.json()
        if 'text' not in data:
            return web.json_response({"result": get_lang('is_required', {'0': 'text'})})
        if 'steps' not in data:
            return web.json_response({"result": get_lang('is_required', {'0': 'steps'})})
        return web.json_response(get_token_counter(data['text'], data['steps']))

    @PromptServer.instance.routes.get("/weilin/physton_prompt/get_data")
    async def _get_data(request):
        key = str(request.query.get('key'))
        data = st.get(key)
        data = privacy_translate_api_config(key, data)
        return web.json_response({"data": data})

    @PromptServer.instance.routes.get("/weilin/physton_prompt/get_datas")
    async def _get_datas(request):
        keys = str(request.query.get('keys'))
        keys = keys.split(',')
        datas = {}
        for key in keys:
            datas[key] = st.get(key)
            datas[key] = privacy_translate_api_config(key, datas[key])
        return web.json_response({"datas": datas})

    @PromptServer.instance.routes.post("/weilin/physton_prompt/set_data")
    async def _set_data(request):
        data = await request.json()
        if 'key' not in data:
            return web.json_response({"success": False, "message": get_lang('is_required', {'0': 'key'})})
        if 'data' not in data:
            return web.json_response({"success": False, "message": get_lang('is_required', {'0': 'data'})})
        data['data'] = unprotected_translate_api_config(data['key'], data['data'])
        st.set(data['key'], data['data'])
        return web.json_response({"success": True})

    @PromptServer.instance.routes.post("/weilin/physton_prompt/set_datas")
    async def _set_datas(request):
        data = await request.json()
        if not isinstance(data, dict):
            return web.json_response({"success": False, "message": get_lang('is_not_dict', {'0': 'data'})})
        for key in data:
            data[key] = unprotected_translate_api_config(key, data[key])
            st.set(key, data[key])
        return web.json_response({"success": True})

    @PromptServer.instance.routes.get("/weilin/physton_prompt/get_data_list_item")
    async def _get_data_list_item(request):
        key = str(request.query.get('key'))
        index = int(request.query.get('index'))
        return web.json_response({"item": st.list_get(key, index)})

    @PromptServer.instance.routes.post("/weilin/physton_prompt/push_data_list")
    async def _push_data_list(request):
        data = await request.json()
        if 'key' not in data:
            return web.json_response({"success": False, "message": get_lang('is_required', {'0': 'key'})})
        if 'item' not in data:
            return web.json_response({"success": False, "message": get_lang('is_required', {'0': 'item'})})
        st.list_push(data['key'], data['item'])
        return web.json_response({"success": True})

    @PromptServer.instance.routes.post("/weilin/physton_prompt/pop_data_list")
    async def _pop_data_list(request):
        data = await request.json()
        if 'key' not in data:
            return web.json_response({"success": False, "message": get_lang('is_required', {'0': 'key'})})
        return web.json_response({"success": True, 'item': st.list_pop(data['key'])})

    @PromptServer.instance.routes.post("/weilin/physton_prompt/shift_data_list")
    async def _shift_data_list(request):
        data = await request.json()
        if 'key' not in data:
            return web.json_response({"success": False, "message": get_lang('is_required', {'0': 'key'})})
        return web.json_response({"success": True, 'item': st.list_shift(data['key'])})

    @PromptServer.instance.routes.post("/weilin/physton_prompt/remove_data_list")
    async def _remove_data_list(request):
        data = await request.json()
        if 'key' not in data:
            return web.json_response({"success": False, "message": get_lang('is_required', {'0': 'key'})})
        if 'index' not in data:
            return web.json_response({"success": False, "message": get_lang('is_required', {'0': 'index'})})
        st.list_remove(data['key'], data['index'])
        return web.json_response({"success": True})

    @PromptServer.instance.routes.post("/weilin/physton_prompt/clear_data_list")
    async def _clear_data_list(request):
        data = await request.json()
        if 'key' not in data:
            return web.json_response({"success": False, "message": get_lang('is_required', {'0': 'key'})})
        st.list_clear(data['key'])
        return web.json_response({"success": True})

    @PromptServer.instance.routes.get("/weilin/physton_prompt/get_histories")
    async def _get_histories(request):
        type = str(request.query.get('type'))
        return web.json_response({"histories": hi.get_histories(type)})

    @PromptServer.instance.routes.get("/weilin/physton_prompt/get_favorites")
    async def _get_favorites(request):
        type = str(request.query.get('type'))
        return web.json_response({"favorites": hi.get_favorites(type)})

    @PromptServer.instance.routes.post("/weilin/physton_prompt/push_history")
    async def _push_history(request):
        data = await request.json()
        if 'type' not in data:
            return web.json_response({"success": False, "message": get_lang('is_required', {'0': 'type'})})
        if 'tags' not in data:
            return web.json_response({"success": False, "message": get_lang('is_required', {'0': 'tags'})})
        if 'prompt' not in data:
            return web.json_response({"success": False, "message": get_lang('is_required', {'0': 'prompt'})})
        hi.push_history(data['type'], data['tags'], data['prompt'], data.get('name', ''))
        return web.json_response({"success": True})

    @PromptServer.instance.routes.post("/weilin/physton_prompt/push_favorite")
    async def _push_favorite(request):
        data = await request.json()
        if 'type' not in data:
            return web.json_response({"success": False, "message": get_lang('is_required', {'0': 'type'})})
        if 'tags' not in data:
            return web.json_response({"success": False, "message": get_lang('is_required', {'0': 'tags'})})
        if 'prompt' not in data:
            return web.json_response({"success": False, "message": get_lang('is_required', {'0': 'prompt'})})
        hi.push_favorite(data['type'], data['tags'], data['prompt'], data.get('name', ''))
        return web.json_response({"success": True})

    @PromptServer.instance.routes.post("/weilin/physton_prompt/move_up_favorite")
    async def _move_up_favorite(request):
        data = await request.json()
        if 'type' not in data:
            return web.json_response({"success": False, "message": get_lang('is_required', {'0': 'type'})})
        if 'id' not in data:
            return web.json_response({"success": False, "message": get_lang('is_required', {'0': 'id'})})
        return web.json_response({"success": hi.move_up_favorite(data['type'], data['id'])})

    @PromptServer.instance.routes.post("/weilin/physton_prompt/move_down_favorite")
    async def _move_down_favorite(request):
        data = await request.json()
        if 'type' not in data:
            return web.json_response({"success": False, "message": get_lang('is_required', {'0': 'type'})})
        if 'id' not in data:
            return web.json_response({"success": False, "message": get_lang('is_required', {'0': 'id'})})
        return web.json_response({"success": hi.move_down_favorite(data['type'], data['id'])})

    @PromptServer.instance.routes.get("/weilin/physton_prompt/get_latest_history")
    async def _get_latest_history(request):
        type = str(request.query.get('type'))
        return web.json_response({"history": hi.get_latest_history(type)})

    @PromptServer.instance.routes.post("/weilin/physton_prompt/set_history")
    async def _set_history(request):
        data = await request.json()
        if 'type' not in data:
            return  web.json_response({"success": False, "message": get_lang('is_required', {'0': 'type'})})
        if 'id' not in data:
            return  web.json_response({"success": False, "message": get_lang('is_required', {'0': 'id'})})
        if 'tags' not in data:
            return  web.json_response({"success": False, "message": get_lang('is_required', {'0': 'tags'})})
        if 'prompt' not in data:
            return  web.json_response({"success": False, "message": get_lang('is_required', {'0': 'prompt'})})
        if 'name' not in data:
            return  web.json_response({"success": False, "message": get_lang('is_required', {'0': 'name'})})
        return  web.json_response({"success": hi.set_history(data['type'], data['id'], data['tags'], data['prompt'], data['name'])})

    @PromptServer.instance.routes.post("/weilin/physton_prompt/set_history_name")
    async def _set_history_name(request):
        data = await request.json()
        if 'type' not in data:
            return  web.json_response({"success": False, "message": get_lang('is_required', {'0': 'type'})})
        if 'id' not in data:
            return  web.json_response({"success": False, "message": get_lang('is_required', {'0': 'id'})})
        if 'name' not in data:
            return  web.json_response({"success": False, "message": get_lang('is_required', {'0': 'name'})})
        return  web.json_response({"success": hi.set_history_name(data['type'], data['id'], data['name'])})

    @PromptServer.instance.routes.post("/weilin/physton_prompt/set_favorite_name")
    async def _set_favorite_name(request):
        data = await request.json()
        if 'type' not in data:
            return  web.json_response({"success": False, "message": get_lang('is_required', {'0': 'type'})})
        if 'id' not in data:
            return  web.json_response({"success": False, "message": get_lang('is_required', {'0': 'id'})})
        if 'name' not in data:
            return  web.json_response({"success": False, "message": get_lang('is_required', {'0': 'name'})})
        return  web.json_response({"success": hi.set_favorite_name(data['type'], data['id'], data['name'])})

    @PromptServer.instance.routes.post("/weilin/physton_prompt/dofavorite")
    async def _dofavorite(request):
        data = await request.json()
        if 'type' not in data:
            return  web.json_response({"success": False, "message": get_lang('is_required', {'0': 'type'})})
        if 'id' not in data:
            return  web.json_response({"success": False, "message": get_lang('is_required', {'0': 'id'})})
        return  web.json_response({"success": hi.dofavorite(data['type'], data['id'])})

    @PromptServer.instance.routes.post("/weilin/physton_prompt/unfavorite")
    async def _unfavorite(request):
        data = await request.json()
        if 'type' not in data:
            return  web.json_response({"success": False, "message": get_lang('is_required', {'0': 'type'})})
        if 'id' not in data:
            return  web.json_response({"success": False, "message": get_lang('is_required', {'0': 'id'})})
        return  web.json_response({"success": hi.unfavorite(data['type'], data['id'])})

    @PromptServer.instance.routes.post("/weilin/physton_prompt/delete_history")
    async def _delete_history(request):
        data = await request.json()
        if 'type' not in data:
            return  web.json_response({"success": False, "message": get_lang('is_required', {'0': 'type'})})
        if 'id' not in data:
            return  web.json_response({"success": False, "message": get_lang('is_required', {'0': 'id'})})
        return  web.json_response({"success": hi.remove_history(data['type'], data['id'])})

    @PromptServer.instance.routes.post("/weilin/physton_prompt/delete_histories")
    async def _delete_histories(request):
        data = await request.json()
        if 'type' not in data:
            return  web.json_response({"success": False, "message": get_lang('is_required', {'0': 'type'})})
        return  web.json_response({"success": hi.remove_histories(data['type'])})

    @PromptServer.instance.routes.post("/weilin/physton_prompt/translate")
    async def _translate(request):
        data = await request.json()
        if 'text' not in data:
            return  web.json_response({"success": False, "message": get_lang('is_required', {'0': 'text'})})
        if 'from_lang' not in data:
            return  web.json_response({"success": False, "message": get_lang('is_required', {'0': 'from_lang'})})
        if 'to_lang' not in data:
            return  web.json_response({"success": False, "message": get_lang('is_required', {'0': 'to_lang'})})
        if 'api' not in data:
            return  web.json_response({"success": False, "message": get_lang('is_required', {'0': 'api'})})
        if 'api_config' not in data:
            return  web.json_response({"success": False, "message": get_lang('is_required', {'0': 'api_config'})})
        return  web.json_response(translate(data['text'], data['from_lang'], data['to_lang'], data['api'], data['api_config'],localLLMTransaltor))

    @PromptServer.instance.routes.post("/weilin/physton_prompt/translates")
    async def _translates(request):
        data = await request.json()
        if 'texts' not in data:
            return  web.json_response({"success": False, "message": get_lang('is_required', {'0': 'texts'})})
        if 'from_lang' not in data:
            return  web.json_response({"success": False, "message": get_lang('is_required', {'0': 'from_lang'})})
        if 'to_lang' not in data:
            return  web.json_response({"success": False, "message": get_lang('is_required', {'0': 'to_lang'})})
        if 'api' not in data:
            return  web.json_response({"success": False, "message": get_lang('is_required', {'0': 'api'})})
        if 'api_config' not in data:
            return  web.json_response({"success": False, "message": get_lang('is_required', {'0': 'api_config'})})
        return  web.json_response(translate(data['texts'], data['from_lang'], data['to_lang'], data['api'], data['api_config'],localLLMTransaltor))

    @PromptServer.instance.routes.get("/weilin/physton_prompt/get_csvs")
    async def _get_csvs(request):
        return  web.json_response({"csvs": get_csvs()})

    @PromptServer.instance.routes.get("/weilin/physton_prompt/get_csv")
    async def _get_csv(request):
        key = str(request.query.get('key'))
        file = get_csv(key)
        if not file:
            return web.Response(status=404)
        filename=os.path.basename(file)
        return web.FileResponse(file)

    @PromptServer.instance.routes.get("/weilin/physton_prompt/styles")
    async def _styles(request):
        file = str(request.query.get('file'))
        file_path = get_style_full_path(file)
        if not file_path or not os.path.exists(file_path):
            return web.Response(status=404)
        filename=os.path.basename(file_path)
        return web.FileResponse(file_path)

    @PromptServer.instance.routes.get("/weilin/physton_prompt/get_extension_css_list")
    async def _get_extension_css_list(request):
        return web.json_response({"css_list": get_extension_css_list()})

    @PromptServer.instance.routes.get("/weilin/physton_prompt/get_extra_networks")
    async def _get_extra_networks(request):
        return web.json_response({"extra_networks": await get_extra_networks()})

    @PromptServer.instance.routes.post("/weilin/physton_prompt/gen_openai")
    async def _gen_openai(request):
        data = await request.json()
        if 'messages' not in data:
            return web.json_response({"success": False, "message": get_lang('is_required', {'0': 'messages'})})
        if 'api_config' not in data:
            return web.json_response({"success": False, "message": get_lang('is_required', {'0': 'api_config'})})
        try:
            return web.json_response({"success": True, 'result': gen_openai(data['messages'], data['api_config'])})
        except Exception as e:
            return web.json_response({"success": False, 'message': str(e)})

    @PromptServer.instance.routes.post("/weilin/physton_prompt/mbart50_initialize")
    async def _mbart50_initialize(request):
        nonlocal localLLMTransaltor
        try:
            if localLLMTransaltor == None:
                localLLMTransaltor = mbart50_translator()
            
            localLLMTransaltor.initialize(True)
            return web.json_response({"success": True})
        except Exception as e:
            return web.json_response({"success": False, 'message': str(e)})

    @PromptServer.instance.routes.get("/weilin/physton_prompt/get_group_tags")
    async def _get_group_tags(request):
        lang = str(request.query.get('lang'))
        return web.json_response({"tags": get_group_tags(lang)})
    
    @PromptServer.instance.routes.post("/weilin/physton_prompt/add_group_tags")
    async def _add_group_tags(request):
        lang = str(request.query.get('lang'))
        data = await request.json()
        try:
            addGroupTag(lang,data['cn'],data['en'],data['key'],data['group'])
        except:
            return web.Response(status=500)
        
        return web.json_response({"info": 'ok'})
    
    @PromptServer.instance.routes.post("/weilin/physton_prompt/edit_group_tags")
    async def _edit_group_tags(request):
        lang = str(request.query.get('lang'))
        data = await request.json()
        try:
            editGroupTag(lang,data['cn'],data['en'],data['key'],data['group'])
        except:
            return web.Response(status=500)
        
        return web.json_response({"info": 'ok'})
    
    @PromptServer.instance.routes.post("/weilin/physton_prompt/delete_group_tags")
    async def _delete_group_tags(request):
        lang = str(request.query.get('lang'))
        data = await request.json()
        try:
            deleteGroupTag(lang,data['cn'],data['en'],data['key'],data['group'])
        except:
            return web.Response(status=500)
        
        return web.json_response({"info": 'ok'})
    
    @PromptServer.instance.routes.post("/weilin/physton_prompt/new_node_group_tags")
    async def _new_node_group_tags(request):
        lang = str(request.query.get('lang'))
        data = await request.json()
        try:
            addNewNodeGroup(lang,data['key'],data['group'],data['color'])
        except:
            return web.Response(status=500)
        
        return web.json_response({"info": 'ok'})
    
    @PromptServer.instance.routes.post("/weilin/physton_prompt/new_group_tags")
    async def _new_group_tags(request):
        lang = str(request.query.get('lang'))
        data = await request.json()
        try:
            addNewGroup(lang,data['key'],data['group'],data['color'])
        except:
            return web.Response(status=500)
        
        return web.json_response({"info": 'ok'})
    
    @PromptServer.instance.routes.post("/weilin/physton_prompt/edit_node_group_tags")
    async def _edit_node_group_tags(request):
        lang = str(request.query.get('lang'))
        data = await request.json()
        try:
            editNodeGroup(lang,data['key'],data['group'])
        except:
            return web.Response(status=500)
        
        return web.json_response({"info": 'ok'})
    
    @PromptServer.instance.routes.post("/weilin/physton_prompt/edit_child_group_tags")
    async def _edit_child_group_tags(request):
        lang = str(request.query.get('lang'))
        data = await request.json()
        try:
            editChildNodeGroup(lang,data['key'],data['group'],data['newgroup'])
        except:
            return web.Response(status=500)
        
        return web.json_response({"info": 'ok'})
    
    @PromptServer.instance.routes.post("/weilin/physton_prompt/delete_node_group_tags")
    async def _delete_node_group_tags(request):
        lang = str(request.query.get('lang'))
        data = await request.json()
        try:
            deleteNodeGroup(lang,data['key'])
        except:
            return web.Response(status=500)
        
        return web.json_response({"info": 'ok'})
    
    @PromptServer.instance.routes.post("/weilin/physton_prompt/delete_child_group_tags")
    async def _delete_child_group_tags(request):
        lang = str(request.query.get('lang'))
        data = await request.json()
        try:
            deleteChildNodeGroup(lang,data['key'],data['group'])
        except:
            return web.Response(status=500)
        
        return web.json_response({"info": 'ok'})

    try:
        translate_api = st.get('translateApi')
        # print(translate_api)
        if translate_api == 'mbart50':
            localLLMTransaltor = mbart50_translator()
    except Exception:
        pass


try:
    on_app_started(on_app_started)
    print('WeiLinComfyUIPromptAllInOne background API service started successfully.')
    print('WeiLinComfyUIPromptAllInOne 插件API已成功启动！')
except Exception as e:
    print(f'WeiLinComfyUIPromptAllInOne background API service failed to start: {e}')
    print(f'WeiLinComfyUIPromptAllInOne 插件API启动失败: {e}')


AUTO_COMPLETE_PATH = os.path.join(os.path.dirname(__file__), "../../../")
sys.path.append(AUTO_COMPLETE_PATH)
from script.autocomplete import runApp
runApp()