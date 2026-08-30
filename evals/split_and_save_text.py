import os
import fitz
import json
from typing import List
from langchain.text_splitter import RecursiveCharacterTextSplitter

def split_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="gpt2", chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_text(text)

def split_and_save_text(pdf_path, chunk_size, chunk_overlap, dest_path):
    try:
        docs = fitz.open(pdf_path)
        pdf_text = ""
        for page_num in range(len(docs)):
            page = docs[page_num]
            page_text = page.get_text("text")
            pdf_text += page_text
        splits = split_text(pdf_text, chunk_size, chunk_overlap)
        with open(dest_path, "w", encoding="utf-8") as f:
            json.dump(splits, f, indent=4)
        return "Successfully split and saved."
    except Exception as e:
        return f"Error occurred: {str(e)}"

if __name__ == "__main__":
    chunk_sizes = [100, 500, 1000, 1500, 2000, 2500, 3000, 3500, 4000]
    chunk_overlap = 50
    pdf_paths = [
        r"evals/data/aHR0cHM6Ly9hcnhpdi5vcmcvcGRmLzE3MDYuMDM3NjJ2Ny5wZGY=\1706.03762v7.pdf",
        r"evals/data/aHR0cHM6Ly9hcnhpdi5vcmcvcGRmLzI1MDIuMTAyNDh2MS5wZGY=\2502.10248v1.pdf",
        r"evals/data/aHR0cHM6Ly9hcnhpdi5vcmcvcGRmLzI0MTEuMDAwODF2MS5wZGY=\2411.00081v1.pdf",
        r"evals/data/aHR0cHM6Ly9hcnhpdi5vcmcvcGRmLzI1MDEuMTM5MjZ2MS5wZGY=\2501.13926v1.pdf",
        r"evals/data/aHR0cHM6Ly9hcnhpdi5vcmcvcGRmLzI0MDUuMDQ0MzR2NS5wZGY=\2405.04434v5.pdf",
        r"evals/data/aHR0cHM6Ly9hcnhpdi5vcmcvcGRmLzI0MDQuMTA3NzR2Mi5wZGY=\2404.10774v2.pdf",
        r"evals/data/aHR0cHM6Ly9hcnhpdi5vcmcvcGRmLzI0MDQuMDUyMjF2Mi5wZGY=\2404.05221v2.pdf",
        r"evals/data/aHR0cHM6Ly9hcnhpdi5vcmcvcGRmLzI0MDIuMTY0MTJ2Mi5wZGY=\2402.16412v2.pdf",
        r"evals/data/aHR0cHM6Ly9hcnhpdi5vcmcvcGRmLzI0MDIuMTQyMDd2Mi5wZGY=\2402.14207v2.pdf",
        r"evals/data/aHR0cHM6Ly9hcnhpdi5vcmcvcGRmLzI0MDEuMTQxOTZ2Mi5wZGY=\2401.14196v2.pdf"
    ]
    dest_folders = [
        r"evals/data/aHR0cHM6Ly9hcnhpdi5vcmcvcGRmLzE3MDYuMDM3NjJ2Ny5wZGY=\text splits",
        r"evals/data/aHR0cHM6Ly9hcnhpdi5vcmcvcGRmLzI1MDIuMTAyNDh2MS5wZGY=\text splits",
        r"evals/data/aHR0cHM6Ly9hcnhpdi5vcmcvcGRmLzI0MTEuMDAwODF2MS5wZGY=\text splits",
        r"evals/data/aHR0cHM6Ly9hcnhpdi5vcmcvcGRmLzI1MDEuMTM5MjZ2MS5wZGY=\text_splits",
        r"evals/data/aHR0cHM6Ly9hcnhpdi5vcmcvcGRmLzI0MDUuMDQ0MzR2NS5wZGY=\text splits",
        r"evals/data/aHR0cHM6Ly9hcnhpdi5vcmcvcGRmLzI0MDQuMTA3NzR2Mi5wZGY=\text splits",
        r"evals/data/aHR0cHM6Ly9hcnhpdi5vcmcvcGRmLzI0MDQuMDUyMjF2Mi5wZGY=\text splits",
        r"evals/data/aHR0cHM6Ly9hcnhpdi5vcmcvcGRmLzI0MDIuMTY0MTJ2Mi5wZGY=\text splits",
        r"evals/data/aHR0cHM6Ly9hcnhpdi5vcmcvcGRmLzI0MDIuMTQyMDd2Mi5wZGY=\text splits",
        r"evals/data/aHR0cHM6Ly9hcnhpdi5vcmcvcGRmLzI0MDEuMTQxOTZ2Mi5wZGY=\text splits"
    ]

    for pdf_path, dest_folder in zip(pdf_paths, dest_folders):
        for chunk_size in chunk_sizes:
            dest_path = os.path.join(dest_folder, f"chunk_size_{chunk_size}.json")
            res = split_and_save_text(pdf_path, chunk_size, chunk_overlap, dest_path)
            if res != "Successfully split and saved.":
                print(f"Failed for {pdf_path} for chunk size {chunk_size}.")