import wx
from PIL import Image, ImageDraw, ImageFont

def nbr_brush(n):
    fn = ImageFont.truetype('calibri.ttf', 14)
    img = Image.new('RGB', (100, 50), color=(255, 255, 255))

    d = ImageDraw.Draw(img)
    w, h = d.textsize(str(n), font=fn)
    pad = 5
    d.text((pad, pad), str(n), font=fn, fill=(0, 0, 0))

    img = img.crop((0, 0, w + 2*pad, h+ 2*pad))
    img.save('nbr_bitmap.png')

    return wx.Brush(wx.Bitmap('nbr_bitmap.png'))
    