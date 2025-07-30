import asyncio
import logging
from dotenv import load_dotenv
import os
from semantic_kernel.functions import kernel_function
from semantic_kernel import Kernel
from semantic_kernel.utils.logging import setup_logging
from semantic_kernel.functions import kernel_function
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, AzureTextCompletion
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import (
    AzureChatPromptExecutionSettings,
)
from semantic_kernel.prompt_template.input_variable import InputVariable
from semantic_kernel.prompt_template import PromptTemplateConfig
from semantic_kernel.functions.kernel_arguments import KernelArguments
from plugins.document_parser_plugin import *

from extractors import extract_fields, extract_text_with_ocr
import glob
import pandas as pd

def initialize_kernel():
    load_dotenv()

    kernel = Kernel()
    text_completion = AzureChatCompletion(
        deployment_name="gpt-4.1-nano",
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        base_url=os.getenv("AZURE_OPENAI_ENDPOINT"),
    )
    kernel.add_service(text_completion)
    return kernel

    

async def classify_document(kernel: Kernel, text: str, execution_settings: AzureChatPromptExecutionSettings):
    prompt_path = "../semanticFunctions/classifyType/classify.txt"
    with open(prompt_path, "r") as f:
        prompt_template = f.read()

    # Create semantic function
    config = PromptTemplateConfig(
        name="classifyDocumentType",
        template=prompt_template,
        description="Identifies the type of document based on the provided text.",
        input_variables=[
        InputVariable(name="input", description="Document content")
    ],
        )

    kernel.add_function(
        function_name="classifyDocumentType",
        plugin_name="ClassifyDocumentPlugin",
        prompt_template_config=config,
    )
    

    args = KernelArguments()
    args["input"] = text 

    result = await kernel.invoke(plugin_name="ClassifyDocumentPlugin", 
                                 function_name="classifyDocumentType", 
                                 arguments=args,
                                 execution_settings=execution_settings)

    return str(result).strip()


async def main():

    kernel = initialize_kernel()

    setup_logging()
    logging.getLogger("kernel").setLevel(logging.DEBUG)

    execution_settings = AzureChatPromptExecutionSettings()
    execution_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()
    kernel.add_function("DocumentParser", extract_text)
    kernel.add_function("DocumentParser", extract_fields_plugin)
   

    document_folder = "../data/documents/"
    file_paths = glob.glob(f"{document_folder}*")

    results = []

    for file_path in file_paths:
        print(f"🔍 Running OCR on {file_path}")
        raw_text = extract_text_with_ocr(file_path)
        # print(f"Extracted Text: {raw_text[:500]}...")  # Print first 500 characters for brevity
        doc_type = await classify_document(kernel, raw_text, execution_settings)
        print(f"Identified Document Type: {doc_type}")

        print("🔎 Extracting structured fields...")
        fields = extract_fields(raw_text, doc_type)

        result = {"file": os.path.basename(file_path), "document_type": doc_type}
        result.update(fields)
        results.append(result)


    for result in results:
        print("\n✅ Extracted Fields:")
        for key, value in result.items():
            print(f"{key}: {value}")
    df = pd.DataFrame(results)
    excel_path = "../data/results.xlsx"
    df.to_excel(excel_path, index=False)
    print(f"\n✅ Results saved to {excel_path}\n")


    # file_path = input("Enter file path to scan: ").strip()
    # print(f"🔍 Running OCR on {file_path}")
    # file_path = "../data/documents/" + file_path  
    # raw_text = extract_text_with_ocr(file_path)
    # print(f"Extracted Text: {raw_text[:500]}...")  # Print first 500 characters for brevity
    # doc_type = await classify_document(kernel, raw_text, execution_settings)
    # print(f"Identified Document Type: {doc_type}")

    # print("🔎 Extracting structured fields...")
    # fields = extract_fields(raw_text, doc_type)

    # print("\n✅ Extracted Fields:")
    # for key, value in fields.items():
    #     print(f"{key}: {value}")   

    # print("\n🔚 Processing complete.")



if __name__ == "__main__":
    asyncio.run(main())


