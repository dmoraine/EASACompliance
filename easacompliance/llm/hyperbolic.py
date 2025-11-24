from crewai import BaseLLM
from typing import Any, Dict, List, Optional, Union
import requests
import json
import re
import time
from requests.exceptions import RequestException
import random
import os

class HyperbolicLLM(BaseLLM):
    def __init__(
        self, 
        model: str,
        api_key: str,
        base_url: str,
        temperature: Optional[float] = 0.1
    ):
        # Initialisation avec les paramètres fournis
        super().__init__(
            model=model,
            temperature=temperature
        )
        
        self.api_key = api_key
        self.endpoint = base_url.rstrip('/')  # Remove trailing slash if present
        self.max_retries = 3  # Nombre maximum de tentatives
        self.initial_delay = 1  # Délai initial en secondes
        
    def _make_request_with_retry(self, url: str, headers: Dict[str, str], payload: Dict[str, Any]) -> requests.Response:
        """Fait une requête avec retry en cas d'erreurs temporaires.
        
        Gère les erreurs suivantes :
        - 408 Request Timeout
        - 429 Too Many Requests
        - 443 Connection Timeout
        - 500 Internal Server Error
        - 502 Bad Gateway
        - 503 Service Unavailable
        - 504 Gateway Timeout
        """
        attempt = 0
        last_exception = None
        
        # Liste des codes d'erreur qui méritent un retry
        retryable_status_codes = {408, 429, 443, 500, 502, 503, 504}
        
        while attempt < self.max_retries:
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                # Log de la requête et de la réponse
                print(f"Request payload: {json.dumps(payload, indent=2)}")
                print(f"Response status: {response.status_code}")
                print(f"Response body: {response.text}")
                
                # Si c'est une erreur qui mérite un retry
                if response.status_code in retryable_status_codes:
                    # Calculer et afficher la taille des messages
                    total_size = sum(len(msg.get("content", "")) for msg in payload.get("messages", []))
                    print(f"Error {response.status_code} - Message size: {total_size} characters")
                    print(f"Number of messages: {len(payload.get('messages', []))}")
                    for i, msg in enumerate(payload.get("messages", [])):
                        print(f"Message {i+1} size: {len(msg.get('content', ''))} characters")
                    
                    # Calculer le délai exponentiel avec un peu de jitter
                    delay = self.initial_delay * (2 ** attempt) * (0.5 + random.random())
                    print(f"Retry attempt {attempt + 1}/{self.max_retries} after {delay:.2f} seconds...")
                    time.sleep(delay)
                    attempt += 1
                    continue
                
                # Si ce n'est pas une erreur qui mérite un retry, on retourne la réponse
                return response
                
            except RequestException as e:
                last_exception = e
                print(f"Request failed: {str(e)}")
                if hasattr(e, 'response') and e.response is not None:
                    print(f"Response text: {e.response.text}")
                
                # Calculer le délai exponentiel avec un peu de jitter
                delay = self.initial_delay * (2 ** attempt) * (0.5 + random.random())
                print(f"Retry attempt {attempt + 1}/{self.max_retries} after {delay:.2f} seconds...")
                time.sleep(delay)
                attempt += 1
        
        # Si on arrive ici, toutes les tentatives ont échoué
        if last_exception:
            raise last_exception
        raise Exception("All retry attempts failed")

    def _convert_tools_to_openai_format(self, tools: List[Any]) -> List[Dict[str, Any]]:
        """Convert CrewAI tools to OpenAI format to prevent hallucinations."""
        openai_tools = []
        
        for tool in tools:
            if hasattr(tool, 'name') and hasattr(tool, 'description'):
                # Format OpenAI standard
                openai_tool = {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    }
                }
                
                # Extract parameters from tool if available
                if hasattr(tool, 'args_schema'):
                    schema = tool.args_schema
                    if hasattr(schema, 'schema'):
                        openai_tool["function"]["parameters"] = schema.schema()
                
                openai_tools.append(openai_tool)
        
        return openai_tools

    def call(
        self,
        messages: Union[str, List[Dict[str, str]]],
        tools: Optional[List[Any]] = None,
        callbacks: Optional[List[Any]] = None,
        available_functions: Optional[Dict[str, Any]] = None,
        **kwargs  # Accept any additional kwargs from CrewAI (like from_task, etc.)
    ) -> Union[str, Any]:
        """Call the Hyperbolic API with the given messages.
        Retourne :
            - str : si le LLM répond avec un contenu textuel
            - Any : le résultat de l'exécution d'un outil si un tool call est détecté
        """
        # Convert string to message format if needed
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]
        
        # Prepare request
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": 2048,  # Valeur par défaut recommandée
            "stream": False
        }
        
        # Add tools if provided and supported - IMPROVED TOOL HANDLING
        if tools and self.supports_function_calling():
            # Convert tools to proper OpenAI format
            openai_tools = self._convert_tools_to_openai_format(tools)
            if openai_tools:
                payload["tools"] = openai_tools
                # Force tool use for critical tools
                payload["tool_choice"] = "auto"
        
        # Make API call with retry
        try:
            response = self._make_request_with_retry(
                f"{self.endpoint}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                payload=payload
            )
            
            response.raise_for_status()
            
            result = response.json()
            
            # Handle tool calls if present
            message = result["choices"][0]["message"]
            text_response = message.get("content", "")
            
            # Check for tool calls
            tool_calls = message.get("tool_calls", [])
            
            # If no tool calls or no available functions, return the text response directly
            if not tool_calls or not available_functions:
                return text_response
            
            # Handle tool calls if present - EXECUTE THE FUNCTION
            tool_result = self._handle_tool_call(tool_calls, available_functions)
            if tool_result is not None:
                return tool_result
            
            # If tool call handling didn't return a result, return text response
            return text_response

        except RequestException as e:
            print(f"Error calling Hyperbolic API: {str(e)}")
            if hasattr(e.response, 'text'):
                print(f"Response text: {e.response.text}")
            raise
    
    def _handle_tool_call(
        self,
        tool_calls: List[Any],
        available_functions: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Handle a tool call from the LLM.
        
        Args:
            tool_calls: List of tool calls from the LLM
            available_functions: Dict of available functions
            
        Returns:
            Optional[str]: The result of the tool call, or None if no tool call was made
        """
        # Validate tool calls and available functions
        if not tool_calls or not available_functions:
            return None
        
        # Extract function name from first tool call
        tool_call = tool_calls[0]
        function_name = tool_call["function"]["name"]
        function_args = {}
        
        # Check if function is available
        if function_name in available_functions:
            try:
                # Parse function arguments
                function_args = json.loads(tool_call["function"]["arguments"])
                fn = available_functions[function_name]
                
                # Execute function
                result = fn(**function_args)
                
                print(f"Tool call executed: {function_name} with args {function_args}")
                return result
            except Exception as e:
                print(f"Error executing function '{function_name}': {e}")
                return None
        
        return None

    def supports_function_calling(self) -> bool:
        """Indique si le modèle supporte l'appel de fonctions."""
        return True
        
    def get_context_window_size(self) -> int:
        """Retourne la taille de la fenêtre de contexte du modèle."""
        return 131069  # Taille de contexte de DeepSeek-V3-0324 selon la doc 