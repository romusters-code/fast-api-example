import torch
from transformers import BertModel, BertTokenizer


class Handler:
    """
    The model handler is responsible for loading the model and tokenizer from the transformers library.
    It also provides methods to embed and compute the similarity between two input texts.
    """

    def __init__(self, model_name: str = "bert-base-uncased") -> None:
        """
        Initialize the model handler.

        A tokenizer and a model are loaded from the Hugging Face Transformers library given the model name.

        :param model_name: Model name to use for loading model with transformers.
        """

        # Load the model and tokenizer with the Hugging Face Transformers library
        self.tokenizer = BertTokenizer.from_pretrained(model_name)
        self.model = BertModel.from_pretrained(model_name)

    def embed(self, text) -> list[float]:
        """
        Embed the input text.

        Embed the input text using the model and return the embedding as a list of floats.

        :param text: The text to embed.
        :return: The embedding of the input text.
        """

        # Forward pass
        tensors = self.forward(text)

        return tensors.tolist()

    def similarity(self, text_1: str, text_2: str) -> float:
        """
        Compute the cosine similarity between two input texts.

        Embed both the input texts using the model and compute the cosine similarity between the two embeddings.

        :param text_1: The first text.
        :param text_2: The second text.
        :return: The similarity score between the two input texts.
        """

        # Forward pass
        tensor_1 = self.forward(text_1)
        tensor_2 = self.forward(text_2)

        # Compute the similarity
        return torch.nn.functional.cosine_similarity(tensor_1, tensor_2, dim=0).item()

    @torch.no_grad()
    def forward(self, text: str) -> torch.Tensor:
        """
        Forward pass of the model.

        Forward the input text through the model and return the last pooling layer.
        This is a tensor of shape (768,).

        :param text: Text to embed.
        :return: Tensor with the last pooling layer.
        """

        # Tokenize the input
        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True)

        # Forward pass
        return self.model(**inputs).pooler_output[0]
