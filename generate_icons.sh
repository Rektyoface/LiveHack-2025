#!/bin/bash

# Create SVG for icon (a simple green "E" in a circle)
cat > icon.svg << 'EOF'
<svg width="128" height="128" xmlns="http://www.w3.org/2000/svg">
  <circle cx="64" cy="64" r="60" fill="#2E7D32"/>
  <text x="64" y="84" font-family="Arial" font-size="80" text-anchor="middle" fill="white">E</text>
</svg>
EOF

# Try to use ImageMagick if available to convert SVG to PNGs
if command -v convert >/dev/null 2>&1; then
  echo "Using ImageMagick to generate icons..."
  convert -background none icon.svg -resize 16x16 extension/icons/icon16.png
  convert -background none icon.svg -resize 48x48 extension/icons/icon48.png
  convert -background none icon.svg -resize 128x128 extension/icons/icon128.png
else
  # Create placeholder colored squares as fallback
  echo "ImageMagick not found. Creating fallback placeholder icons..."
  
  # Function to create a colored square
  create_color_square() {
    size=$1
    output=$2
    
    # Create a simple colored square image with text
    cat > $output << EOF
<svg width="$size" height="$size" xmlns="http://www.w3.org/2000/svg">
  <rect width="100%" height="100%" fill="#2E7D32"/>
  <text x="50%" y="50%" font-family="Arial" font-size="$(($size/2))" text-anchor="middle" dominant-baseline="middle" fill="white">E</text>
</svg>
EOF
  }
  
  # Create icons in the three required sizes
  create_color_square 16 "extension/icons/icon16.svg"
  create_color_square 48 "extension/icons/icon48.svg"
  create_color_square 128 "extension/icons/icon128.svg"
  
  echo "Created SVG icon placeholders. In a production environment, convert these to PNG."
fi

echo "Icon generation complete."
