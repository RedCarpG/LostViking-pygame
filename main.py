# Entry point for the web build (pygbag requires a main.py at the project root)
import asyncio

# pygbag only scans this file to know which packages to preload in the browser
import pygame

from src.main import main

asyncio.run(main())
