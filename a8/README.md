## Assignment 8

- Add support for Gmail, Telegram, GDrive (manage your credentials well)
- Sent message to your Agent on Telegram: "Find the Current Point Standings of F1 Racers, then put that into a Google Excel Sheet, and then share the link to this sheet with me (Your email id) on Gmail"
- One of the servers that you add must be an SSE server
- Share the YouTube Video of this working
- Share the link to your GitHub Code (remove confidential information)


## Target

- Add support for gmail integration
- Add support of telegram integration (SSE Server)
- Ollama run on the system and connect LLM using it or gemini
- Prepare the prompt in such a way that it can use tools websearch
- Figure out websearch via browser (Duckduckgo api)

## Steps


- Get message from telegram via sse connection
- tool discovery - websearch, send_email
- intent extraction 
- web search - websearch