// Keep the inherited wall pixel-for-pixel outside the new image-tool mark.
const fs = require('node:fs');
const crypto = require('node:crypto');
const media = require('../line-1/media/finish-wall.cjs');
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const oldBytes = fs.readFileSync('artifacts/gathering/wall-v13.png');
const generatedBytes = fs.readFileSync('artifacts/gathering/wall-v14.png');
const old = media.decode(oldBytes), generated = media.decode(generatedBytes);
const output = {...old, pixels: Buffer.from(old.pixels)};
// The new pouch sits entirely on previously bare stone, left of Pepe.
const box = [104, 735, 123, 176];
let changed = 0, protectedChanged = 0;
for (let y=0;y<old.height;y++) for(let x=0;x<old.width;x++) {
  const [left,top,width,height] = box;
  const edge = Math.min(x-left, left+width-1-x, y-top, top+height-1-y);
  const alpha = Math.max(0,Math.min(1,edge/7));
  const i = (y*old.width+x)*3;
  for(let c=0;c<3;c++) output.pixels[i+c]=Math.round(old.pixels[i+c]*(1-alpha)+generated.pixels[i+c]*alpha);
  if(!old.pixels.subarray(i,i+3).equals(output.pixels.subarray(i,i+3))) {
    changed++;
    if(edge<0) protectedChanged++;
  }
}
if(changed<1000 || protectedChanged) throw Error('mark missing or inheritance altered');
const wall = media.encode(output), preview = media.thumbnail(output);
if(!media.decode(wall).pixels.equals(output.pixels) || preview.length>100000) throw Error('encoding failed');
fs.writeFileSync('artifacts/gathering/wall-v14.png',wall);
fs.writeFileSync('dist/gathering/33.jpg',preview);
fs.unlinkSync('artifacts/gathering/wall.png');
fs.symlinkSync('wall-v14.png','artifacts/gathering/wall.png');
const evidence={previous_sha256:hash(oldBytes),generated_sha256:hash(generatedBytes),wall_sha256:hash(wall),
  dimensions:[old.width,old.height],format:'RGB PNG',png_bytes:wall.length,jpeg_dimensions:[512,512],
  jpeg_bytes:preview.length,mark_rectangle:box,changed_pixels:changed,pixels_changed_outside:protectedChanged,
  method:'Imagegen additive edit, restricted to bare lower-left rock with a seven-pixel feather; inherited pixels outside the patch are exact.'};
fs.writeFileSync('gathering/preservation-33.json',JSON.stringify(evidence,null,2)+'\n');
const record={name:'Four Seeds Kept Together',image:'https://api.imd.fun/artifacts/'+hash(wall),attributes:[
  {trait_type:'Cave',value:'Lava'},{trait_type:'Wall',value:'Gathering'},{trait_type:'Number',value:33},
  {trait_type:'Left behind',value:'Approved ZIP parameter compatibility handoff'},
  {trait_type:'Meaning',value:'Four chalk seeds rest in one ochre pouch, keeping separate gifts safe for the next worker.'},
  {trait_type:'One thing',value:'Gathering'}]};
fs.writeFileSync('dist/gathering/33.json',JSON.stringify(record,null,2)+'\n');
console.log(JSON.stringify(evidence,null,2));
