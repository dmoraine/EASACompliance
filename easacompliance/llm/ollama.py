from crewai import BaseLLM
from typing import Any, Dict, List, Optional, Union
import requests
import json
from requests.exceptions import RequestException

class OllamaLLM(BaseLLM):
    """Custom LLM wrapper for Ollama local models.
    
    This class bypasses litellm and directly calls Ollama's OpenAI-compatible API.
    Ollama doesn't require an API key, so we can use any dummy value or omit it.
    """
    
    def __init__(
        self, 
        model: str,
        base_url: str = "http://localhost:11434/v1",
        api_key: Optional[str] = None,  # Not used for Ollama, but kept for compatibility
        temperature: Optional[float] = 0.1
    ):
        super().__init__(
            model=model,
            temperature=temperature
        )
        
        self.endpoint = base_url.rstrip('/')  # Remove trailing slash if present
        self.max_retries = 3
        self.initial_delay = 1
        
    def _make_request_with_retry(self, url: str, headers: Dict[str, str], payload: Dict[str, Any]) -> requests.Response:
        """Make a request with retry logic for temporary errors."""
        attempt = 0
        last_exception = None
        
        retryable_status_codes = {408, 429, 500, 502, 503, 504}
        
        while attempt < self.max_retries:
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=60  # Ollama can be slower, use longer timeout
                )
                
                # If it's a retryable error, retry
                if response.status_code in retryable_status_codes:
                    if attempt < self.max_retries - 1:
                        import time
                        delay = self.initial_delay * (2 ** attempt)
                        time.sleep(delay)
                        attempt += 1
                        continue
                
                return response
                
            except RequestException as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    import time
                    delay = self.initial_delay * (2 ** attempt)
                    time.sleep(delay)
                    attempt += 1
                else:
                    break
        
        if last_exception:
            raise last_exception
        raise Exception("All retry attempts failed")

    def _convert_tools_to_openai_format(self, tools: List[Any]) -> List[Dict[str, Any]]:
        """Convert CrewAI tools to OpenAI format."""
        openai_tools = []
        
        for tool in tools:
            if hasattr(tool, 'name') and hasattr(tool, 'description'):
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
        **kwargs
    ) -> Union[str, Any]:
        """Call the Ollama API with the given messages."""
        # Convert string to message format if needed
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]
        
        # Prepare request
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "stream": False
        }
        
        # Add tools if provided
        if tools and self.supports_function_calling():
            openai_tools = self._convert_tools_to_openai_format(tools)
            if openai_tools:
                payload["tools"] = openai_tools
                payload["tool_choice"] = "auto"
        
        # Ollama doesn't require authentication, but some implementations expect a header
        headers = {
            "Content-Type": "application/json"
        }
        
        # Make API call with retry
        try:
            response = self._make_request_with_retry(
                f"{self.endpoint}/chat/completions",
                headers=headers,
                payload=payload
            )
            
            response.raise_for_status()
            
            result = response.json()
            
            # Handle tool calls if present
            message = result["choices"][0]["message"]
            text_response = message.get("content", "")
            
            # Check for tool calls
            tool_calls = message.get("tool_calls", [])
            
            # If no tool calls or no available functions, return the text response
            if not tool_calls or not available_functions:
                return text_response
            
            # Handle tool calls if present
            tool_result = self._handle_tool_call(tool_calls, available_functions)
            if tool_result is not None:
                return tool_result
            
            return text_response

        except RequestException as e:
            error_msg = f"Error calling Ollama API: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_msg += f" - Response: {e.response.text}"
                except:
                    pass
            raise Exception(error_msg) from e
    
    def _handle_tool_call(
        self,
        tool_calls: List[Any],
        available_functions: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Handle a tool call from the LLM."""
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
                
                return result
            except Exception as e:
                print(f"Error executing function '{function_name}': {e}")
                return None
        
        return None

    def supports_function_calling(self) -> bool:
        """Indicate if the model supports function calling."""
        return True
        
    def get_context_window_size(self) -> int:
        """Return the context window size of the model."""
        # Most Ollama models have at least 8k context, many have 32k+
        # Using a conservative default
        return 8192


