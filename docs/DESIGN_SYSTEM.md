# PAGie Design System - Quick Reference

## 🎨 Color Palette (Modern Theme)

### Primary Colors
```css
Primary:      #6366f1  /* Indigo */
Primary Dark: #4338ca  /* Deep Indigo */
Accent:       #ec4899  /* Pink */
```

### Background Colors
```css
Secondary:    #f0f9ff  /* Light blue */
Border:       #e0e7ff  /* Soft indigo */
Background:   #fafbff  /* Very light blue-white */
```

### Status Colors
```css
Success:      #10b981  /* Green */
Warning:      #f59e0b  /* Amber */
Error:        #ef4444  /* Red */
Info:         #3b82f6  /* Blue */
```

### Text Colors
```css
Primary Text:   #1e293b  /* Dark slate */
Secondary Text: #64748b  /* Slate */
```

### Gradients
```css
Header:   linear-gradient(120deg, #6366f1 0%, #8b5cf6 50%, #ec4899 100%)
Primary:  linear-gradient(135deg, #667eea 0%, #764ba2 100%)
Accent:   linear-gradient(135deg, #f093fb 0%, #f5576c 100%)
Soft:     linear-gradient(135deg, #e0c3fc 0%, #8ec5fc 100%)
```

## 📏 Spacing Scale

```css
XS:  0.25rem  (4px)
SM:  0.5rem   (8px)
MD:  1rem     (16px)
LG:  1.5rem   (24px)
XL:  2rem     (32px)
2XL: 3rem     (48px)
```

## 🔤 Typography

### Fonts
```css
Body:  'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif
Code:  'JetBrains Mono', monospace
```

### Font Sizes
```css
XS:   0.7rem   (11px)
SM:   0.75rem  (12px)
BASE: 0.875rem (14px)
MD:   1rem     (16px)
LG:   1.25rem  (20px)
XL:   1.5rem   (24px)
2XL:  1.75rem  (28px)
3XL:  2rem     (32px)
4XL:  2.5rem   (40px)
```

### Font Weights
```css
Light:     300
Regular:   400
Medium:    500
Semibold:  600
Bold:      700
```

## 📦 Border Radius

```css
SM:  8px   /* Small elements */
MD:  10px  /* Inputs */
LG:  12px  /* Cards */
XL:  16px  /* Chat bubbles */
2XL: 20px  /* Hero sections */
```

## 🌑 Shadows

### Subtle
```css
box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
```

### Default
```css
box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
```

### Medium
```css
box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
```

### Strong
```css
box-shadow: 0 8px 24px rgba(99, 102, 241, 0.2);
```

### Colored (Brand)
```css
box-shadow: 0 4px 12px rgba(99, 102, 241, 0.2);  /* Indigo */
box-shadow: 0 4px 12px rgba(236, 72, 153, 0.2);  /* Pink */
```

## ⏱️ Animations

### Duration
```css
Fast:    0.2s
Medium:  0.3s
Slow:    0.5s
```

### Easing
```css
Default:  ease
Smooth:   cubic-bezier(0.4, 0, 0.2, 1)
```

### Common Transforms
```css
Lift:   translateY(-2px)
Pop:    scale(1.02)
Down:   translateY(0px)
```

## 🎯 Component Patterns

### Card
```css
background: white;
border-radius: 12px;
padding: 1rem;
box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
border: 1px solid rgba(0, 0, 0, 0.05);
transition: all 0.2s ease;
```

### Gradient Button
```css
background: linear-gradient(120deg, #6366f1, #8b5cf6, #ec4899);
color: white;
border: none;
border-radius: 12px;
padding: 0.75rem 1.5rem;
font-weight: 600;
box-shadow: 0 4px 12px rgba(99, 102, 241, 0.2);
transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

&:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(99, 102, 241, 0.3);
}
```

### Glassmorphism Badge
```css
background: rgba(99, 102, 241, 0.1);
backdrop-filter: blur(10px);
border: 1px solid rgba(99, 102, 241, 0.2);
border-radius: 8px;
padding: 6px 12px;
transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

&:hover {
  background: rgba(99, 102, 241, 0.15);
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.2);
}
```

### Status Card
```css
background: #ecfdf5;  /* Success green tint */
border: 2px solid #10b98130;
border-radius: 12px;
padding: 1rem;
```

### Gradient Text
```css
background: linear-gradient(120deg, #6366f1, #8b5cf6, #ec4899);
-webkit-background-clip: text;
-webkit-text-fill-color: transparent;
background-clip: text;
font-weight: 700;
```

## 🔄 State Variations

### Hover States
```css
Button:    translateY(-2px) + enhanced shadow
Badge:     background opacity increase + lift
Card:      enhanced shadow + subtle lift
Link:      color change + underline
```

### Active States
```css
Button:    translateY(0) + reduced shadow
Tab:       background change + shadow
Input:     border color + shadow glow
```

### Disabled States
```css
opacity: 0.5;
cursor: not-allowed;
pointer-events: none;
```

## 📱 Responsive Breakpoints

```css
Mobile:   < 768px
Tablet:   768px - 1024px
Desktop:  > 1024px
```

## 🎨 Theme Switching

### Available Themes
1. **Modern**: Indigo/Purple/Pink
2. **Ocean**: Sky Blue/Cyan/Teal
3. **Sunset**: Amber/Red/Pink
4. **Forest**: Emerald/Green/Light Green

### How to Switch
In `app_modular.py`:
```python
apply_custom_styles(theme="modern")  # Change here
```

## 🛠️ Quick Customization Guide

### Change Primary Color
```python
# In ui/styles/themes.py
"primary": "#your-hex-color",
```

### Adjust Animation Speed
```css
/* Find and replace in themes.py */
transition: all 0.2s ease;  /* Make faster/slower */
```

### Modify Border Radius
```css
/* Search for border-radius values */
border-radius: 12px;  /* Increase for rounder */
```

### Update Shadows
```css
/* Adjust rgba opacity for lighter/darker */
box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
```

---

**Quick Reference for PAGie Design System**  
*Keep this handy while customizing the UI*
