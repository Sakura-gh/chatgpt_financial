import os; #os.environ['no_proxy'] = '*' # 避免代理网络产生意外污染
import gradio as gr
from predict import predict
from toolbox import format_io, find_free_port, on_file_uploaded, on_report_generated, get_conf

# 建议您复制一个config_private.py放自己的秘密, 如API和代理网址, 避免不小心传github被别人看到
proxies, WEB_PORT, LLM_MODEL, CONCURRENT_COUNT, AUTHENTICATION, CHATBOT_HEIGHT = \
    get_conf('proxies', 'WEB_PORT', 'LLM_MODEL', 'CONCURRENT_COUNT', 'AUTHENTICATION', 'CHATBOT_HEIGHT')

# 如果WEB_PORT是-1, 则随机选取WEB端口
PORT = find_free_port() if WEB_PORT <= 0 else WEB_PORT
if not AUTHENTICATION: AUTHENTICATION = None

initial_prompt = "Serve me as a financial assistant."
title_html = """<h1 align="center">ChatGPT 金融小助手</h1>"""

# 问询记录, python 版本建议3.9+（越新越好）
import logging
os.makedirs("gpt_log", exist_ok=True)
try:logging.basicConfig(filename="gpt_log/chat_secrets.log", level=logging.INFO, encoding="utf-8")
except:logging.basicConfig(filename="gpt_log/chat_secrets.log", level=logging.INFO)
print("所有问询记录将自动保存在本地目录./gpt_log/chat_secrets.log, 请注意自我隐私保护哦！")

# 一些普通功能模块
from functional import get_functionals
functional = get_functionals()

# 处理markdown文本格式的转变
gr.Chatbot.postprocess = format_io

# 做一些外观色彩上的调整
from theme import adjust_theme, advanced_css
set_theme = adjust_theme()

cancel_handles = []
with gr.Blocks(theme=set_theme, analytics_enabled=False, css=advanced_css) as demo:
    gr.HTML(title_html)
    with gr.Row().style(equal_height=True):
        with gr.Column(scale=2):
            with gr.Row():
                chatbot = gr.Chatbot()
                chatbot.style(height=CHATBOT_HEIGHT)
                history = gr.State([])
            with gr.Row():
                with gr.Column(scale=6):
                    txt = gr.Textbox(show_label=False, placeholder="Input question here.").style(container=False)
                with gr.Column(scale=1):
                    # 备选 ✅⬆️✔️
                    submitBtn = gr.Button("确定", variant="primary");            
        with gr.Column(scale=1):
            with gr.Row():
                resetBtn = gr.Button("重置", variant="secondary"); resetBtn.style(size="sm")
                stopBtn = gr.Button("停止", variant="secondary"); stopBtn.style(size="sm")
            with gr.Row():
                # with gr.Accordion("上传本地文件可供金融小助手解析使用。", open=True) as area_file_up:
                file_upload = gr.Files(label="上传本地文件可供金融小助手解析使用，推荐上传压缩文件(zip, tar)", file_count="multiple")
            with gr.Row():
                from check_proxy import check_proxy
                status = gr.Markdown(f"Tip: 按Enter提交, 按Shift+Enter换行。当前模型: {LLM_MODEL} \n {check_proxy(proxies)}")
            with gr.Accordion("基础功能区", open=True) as area_basic_fn:
                with gr.Row():
                    for k in functional:
                        variant = functional[k]["Color"] if "Color" in functional[k] else "secondary"
                        functional[k]["Button"] = gr.Button(k, variant=variant)
            with gr.Accordion("展开SysPrompt & GPT参数", open=False):
                system_prompt = gr.Textbox(show_label=True, placeholder=f"System Prompt", label="System prompt", value=initial_prompt)
                top_p = gr.Slider(minimum=-0, maximum=1.0, value=1.0, step=0.01,interactive=True, label="Top-p (nucleus sampling)",)
                temperature = gr.Slider(minimum=-0, maximum=2.0, value=1.0, step=0.01, interactive=True, label="Temperature",)


    # 整理反复出现的控件句柄组合
    input_combo = [txt, top_p, temperature, chatbot, history, system_prompt]
    output_combo = [chatbot, history, status]
    predict_args = dict(fn=predict, inputs=input_combo, outputs=output_combo)
    empty_txt_args = dict(fn=lambda: gr.update(value=''), inputs=[], outputs=[txt]) # 用于在提交后清空输入栏
    # 提交按钮、重置按钮
    cancel_handles.append(txt.submit(**predict_args))
    cancel_handles.append(submitBtn.click(**predict_args))
    submitBtn.click(**empty_txt_args) # 在提交后清空输入栏
    txt.submit(**empty_txt_args) # 在提交后清空输入栏
    resetBtn.click(lambda: ([], [], "已重置"), None, output_combo)
    # 基础功能区的回调函数注册
    for k in functional:
        click_handle = functional[k]["Button"].click(functional[k]["Function"], [*input_combo, gr.State(PORT)], output_combo)
        click_handle.then(on_report_generated, [file_upload, chatbot], [file_upload, chatbot])
        cancel_handles.append(click_handle)
    # 文件上传区，接收文件后与chatbot的互动
    file_upload.upload(on_file_uploaded, [file_upload, chatbot, txt], [chatbot, txt])

    # 终止按钮的回调函数注册
    stopBtn.click(fn=None, inputs=None, outputs=None, cancels=cancel_handles)

# gradio的inbrowser触发不太稳定，回滚代码到原始的浏览器打开函数
def auto_opentab_delay():
    import threading, webbrowser, time
    print(f"如果浏览器没有自动打开，请复制并转到以下URL: http://localhost:{PORT}")
    def open(): 
        time.sleep(2)
        webbrowser.open_new_tab(f"http://localhost:{PORT}")
    threading.Thread(target=open, name="open-browser", daemon=True).start()

auto_opentab_delay()
demo.title = "ChatGPT 金融小助手"
demo.queue(concurrency_count=CONCURRENT_COUNT).launch(server_name="0.0.0.0", share=False, server_port=PORT, auth=AUTHENTICATION)
