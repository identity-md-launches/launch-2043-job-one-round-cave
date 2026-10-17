// Local pigment composition. Only inherited wall and generated motif are read.
const fs=require('node:fs'),crypto=require('node:crypto'),cp=require('node:child_process');
const {decode,encode,thumbnail}=require('../../line-1/media/finish-wall.cjs');
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const oldBytes=fs.readFileSync('artifacts/line-4/wall-v13.png');
if(JSON.parse(fs.readFileSync('dist/line-4/32.json')).image!==
 'https://api.imd.fun/artifacts/'+hash(oldBytes))throw Error('ancestor mismatch');
const draft=fs.readFileSync('artifacts/line-4/wall-v14.png');
const width=draft.readUInt32BE(16),height=draft.readUInt32BE(20);
const decoded=cp.spawnSync('/opt/tools/bin/ffmpeg',[
 '-v','error','-i','pipe:0','-f','rawvideo','-pix_fmt','rgb24','pipe:1'],
 {input:draft,maxBuffer:32*1024*1024});
if(decoded.status!==0||decoded.stdout.length!==width*height*3)throw Error('motif decode failed');
const gen=decoded.stdout,old=decode(oldBytes),out={...old,pixels:Buffer.from(old.pixels)};
// Bare rock above the two inherited schema tablets. Neither the frog nor any
// ancestral pigment falls in this small rectangle.
const bounds=[750,530,890,590];
let changed=0;
for(let y=bounds[1];y<=bounds[3];y++)for(let x=bounds[0];x<=bounds[2];x++){
 const sx0=65+(x-bounds[0])*1400/141,sy0=255+(y-bounds[1])*455/61;
 const sx1=sx0+1400/141,sy1=sy0+455/61;
 let n=0,yellow=0,red=0;
 for(let sy=Math.floor(sy0);sy<Math.ceil(sy1);sy++)for(let sx=Math.floor(sx0);sx<Math.ceil(sx1);sx++){
  const j=(sy*width+sx)*3,r=gen[j],g=gen[j+1],b=gen[j+2];
  n++;
  if(r>175&&g>90&&g/r>.48&&b/g<.55)yellow++;
  else if(r>135&&g<95&&g/r<.48&&b/r<.25)red++;
 }
 const j=(y*old.width+x)*3;
 const grain=.65+.35*(old.pixels[j]+old.pixels[j+1])/510;
 const ay=.9*grain*yellow/n,ar=.8*grain*red/n,a=ay+ar;
 for(let c=0;c<3;c++)out.pixels[j+c]=Math.round(old.pixels[j+c]*(1-a)+[199,137,47][c]*ay+[147,57,29][c]*ar);
 if(!out.pixels.subarray(j,j+3).equals(old.pixels.subarray(j,j+3)))changed++;
}
let outside=0;
for(let y=0;y<old.height;y++)for(let x=0;x<old.width;x++){
 if(x>=bounds[0]&&x<=bounds[2]&&y>=bounds[1]&&y<=bounds[3])continue;
 const j=(y*old.width+x)*3;
 if(!old.pixels.subarray(j,j+3).equals(out.pixels.subarray(j,j+3)))outside++;
}
if(outside||changed<500)throw Error('preservation or addition failed');
const png=encode(out),jpg=thumbnail(out);
if(jpg.length>100000||!decode(png).pixels.equals(out.pixels))throw Error('encode failed');
fs.writeFileSync('artifacts/line-4/wall-v14.png',png);
fs.unlinkSync('artifacts/line-4/wall.png');
fs.linkSync('artifacts/line-4/wall-v14.png','artifacts/line-4/wall.png');
fs.writeFileSync('dist/line-4/33.jpg',jpg);
const review={ancestor_sha256:hash(oldBytes),generated_motif_sha256:hash(draft),
 wall:'artifacts/line-4/wall-v14.png',canonical_wall:'artifacts/line-4/wall.png',
 sha256:hash(png),dimensions:[old.width,old.height],format:'RGB PNG',bytes:png.length,
 preview:'dist/line-4/33.jpg',preview_dimensions:[512,512],preview_format:'JPEG',preview_bytes:jpg.length,
 preview_sha256:hash(jpg),addition_bounds_inclusive:bounds,changed_pixels:changed,
 pixels_changed_outside_addition:outside,png_roundtrip_passed:true,
 method:'Installed image generator; pigment sampled and blended onto inherited rock, no generated background retained.',
 prompt:'Two ochre braided cords: three separated red beads on one, three grouped beads on the other. Handmade worn earth pigment on rock, no writing or hands.',
 visual_review:'Pending full wall and thumbnail inspection.',
 unmet_visual_requirements:['Inherited photographic rock texture retained to preserve the existing wall.']};
fs.writeFileSync('line-4/review-33.json',JSON.stringify(review,null,2)+'\n');
console.log(JSON.stringify(review,null,2));
