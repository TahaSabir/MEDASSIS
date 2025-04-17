# backend/model_utils.py

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

def load_model():
    model_name = "Henrychur/MMed-Llama-3-8B"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float16)
    return tokenizer, model
