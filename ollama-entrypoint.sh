#!/bin/sh
ollama serve &
sleep 2
ollama pull qwen2.5:1.5b
wait
