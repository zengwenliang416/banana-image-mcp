# Assets

This directory contains visual assets for the project README.

## Required Files

### logo.png
- **Size**: 120x120 pixels (or larger, will be scaled)
- **Format**: PNG with transparent background
- **Style**: A banana-themed icon representing AI image generation

### demo.gif
- **Size**: ~700px width
- **Format**: GIF
- **Content**: Screen recording showing:
  1. User typing a prompt in Claude Desktop
  2. The image generation in progress
  3. The final generated image displayed

## Creating Assets

### Logo Options

1. **AI Generated**: Use the project itself to generate a logo:
   ```
   "Generate a minimalist logo: a banana with a paintbrush, flat design, tech style, transparent background"
   ```

2. **Simple Text Logo**: Use a tool like Figma/Canva to create a simple text-based logo

3. **Placeholder**: Until a logo is created, the README will show a broken image link

### Demo GIF

1. Use a screen recording tool (QuickTime on Mac, OBS, etc.)
2. Record yourself using the MCP server in Claude Desktop
3. Convert to GIF using `ffmpeg` or a tool like Gifski
4. Optimize the file size (aim for under 5MB)

## Notes

- Keep file sizes reasonable for fast README loading
- Use descriptive alt text in the README for accessibility
