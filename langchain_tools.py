from langchain import PromptTemplate, LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains.mapreduce import MapReduceChain
from langchain.prompts import PromptTemplate
from langchain.docstore.document import Document
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)

import os # TODO: delete
os.environ['OPENAI_API_KEY']="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"



def summerize_one_file(origin_text):
    import os

    chat = ChatOpenAI(temperature=0)
    # 文档分为多个块，每个块等待分别总结
    text_splitter = CharacterTextSplitter.from_tiktoken_encoder(        
                    separator = "\n\n",
                    chunk_size = 1500,
                    chunk_overlap  = 200,)
    texts = text_splitter.split_text(origin_text)

    chat = ChatOpenAI(temperature=0)
    # 分批总结文档
    batch_messages = [[
        SystemMessage(content="You are a helpful assistant to summarize paragraphs from user."),
        HumanMessage(content=text)
    ]for text in texts]
    result = chat.generate(batch_messages)

    # 将次级文档重新整合起来
    sub_summerized = '\n'.join([str(i+1) + '.' + generation[0].text for i,generation in enumerate(result.generations)])

    return sub_summerized


import asyncio
from langchain.llms import OpenAI

async def openai_concurrently(contents):
    '''用于异步调用openai llm
    异步调用示例：output = asyncio.run(openai_concurrently([['hi'], ['how are you'], ['who are you']]))
    output: [LLMResult, ...]  
    LLMResult.generations[0][0].text是llm的输出文本
    '''
    llm = OpenAI()
    # 定义子任务
    async def async_generate(llm, content):
        return await llm.agenerate(content)
    tasks = [async_generate(llm, content) for content in contents]
    # 异步运行并整合输出
    return await asyncio.gather(*tasks) 

async def chatopenai_concurrently(batch_messages):
    '''用于异步调用openai chat llm
    异步调用示例：output = asyncio.run(chatopenai_concurrently([
                                    [[SystemMessage(content="You are a helpful assistant that translates English to French."),
                                    HumanMessage(content="Translate this sentence from English to French. I love programming.")]],
                                    [[SystemMessage(content="You are a helpful assistant that translates English to French."),
                                    HumanMessage(content="Translate this sentence from English to French. I love artificial intelligence.")],]]))
    注意此版本的langchain必须用两层嵌套括号输入
    output: [LLMResult, ...]  
    LLMResult.generations[0][0].text是llm的输出文本
    '''
    chat = ChatOpenAI()
    # 定义子任务
    async def async_generate(chat, messages):
        return await chat.agenerate(messages)
    tasks = [async_generate(chat, messages) for messages in batch_messages]
    # 异步运行并整合输出
    return await asyncio.gather(*tasks) 


async def split2json(files):
    '''用于异步将多个文件分chunk、存储并提取总结信息。
    '''
    from langchain.document_loaders import PyPDFLoader
    from langchain.docstore.document import Document
    import json
    text_splitters = [
        CharacterTextSplitter.from_tiktoken_encoder(separator = ".", chunk_size = 1500, chunk_overlap  = 0,),
        CharacterTextSplitter.from_tiktoken_encoder(separator = "。", chunk_size = 1500, chunk_overlap  = 0,),
        CharacterTextSplitter.from_tiktoken_encoder(separator = "\n", chunk_size = 1500, chunk_overlap  = 0,),
    ]

    # 定义子任务
    async def async_chunked(text_splitters, file):
        print('正在运行并行')
        loader_pdf = PyPDFLoader(file)
        pages = loader_pdf.load_and_split()
        content = ''.join([page.page_content for page in pages])
        page_lens = [len(page.page_content) for page in pages]
        
        for text_splitter in text_splitters:
            chunks = text_splitter.split_text(content)
            chunk_lens = [len(chunk) for chunk in chunks]
            if all([lens<12000 for lens in chunk_lens]):
                break
        # create json file
        path_base, extension = os.path.splitext(file)
        json_name = path_base + '_chunk.json'
        json_dict = {'file':os.path.basename(file),
                     'content':content,
                     'page_lens':page_lens,
                     'chunk_lens':chunk_lens,}
        with open(json_name, 'w') as file:
            file.write(json.dumps(json_dict))   
        return json_name
    
    tasks = [async_chunked(text_splitters, file) for file in files]
    # 异步运行并整合输出
    return await asyncio.gather(*tasks)

# asyncio.run(split2json(files))

        

        




    

