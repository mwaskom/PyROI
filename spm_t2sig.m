function spm_t2sig(concell)
% Convert SPM T maps to -log10(P) maps
% 
% Usage: spm_t2sig(concell)  
% 
% Inputs:
%   concell : cell array of paths to SPM contrast directories
%
% This function will convert all spmT images in an arbitrary number 
% of contrast directories to -log10(P) images. It expects to read 
% .img files, and writes to .nii.
%  
% Note that this function requires SPM to be on your path, and that 
% it was developed with SPM 8. It also uses the tTest function 
% provided in the FsFast toolbox with the Freesurfer distribution. 
% ____________________________________________________________________________________
% $ Written by Michael Waskom -- mwaskom@mit.edu $

% Print usage
if nargin==0, fprintf('\n   spm_t2sig(contrast directories)\n\n'); return; end

% Check that tTest.m exists and error out with something informative if not
fsfasthome = getenv('FSFAST_HOME');
fsfasttb = sprintf('%s/toolbox',fsfasthome);
if ~exist(sprintf('%s/tTest.m',fsfasttb),'file')
    fprinft('\n  Error: could not find tTest.m in the FsFast toolbox\n\n');
    return
end

% Convert the input to a cell if it's just a string
if isa(concell,'char'), concell = {concell}; end

% Iterate through the contrast directories and convert to sig
for iCon = 1:length(concell), convert_tmaps(concell{iCon}); end


function convert_tmaps(contrastdir)
% Subroutine for actually performing the conversion from T map to sig map.
% This function converts all spmT files in a given contrast directory

% Get the list of spmT images in this contrast dir
fullimginfo = dir([contrastdir '/spmT*.img']);
for i=1:length(fullimginfo)
    imgs{i} = fullfile(contrastdir,fullimginfo(i).name);
end

% Get the DOF for this paradigm from the descr string of the first volume
spmread = spm_vol(imgs{1});
t = regexp(spmread.descrip,'\[([0-9\.]*)\]','tokens')
dof = str2num(t{1}{1})

% Read in each image, convert to -log10(p), change sign, and write
for iFile = 1:length(imgs)
    fprintf('Reading %s\n',imgs{iFile});
    spmThead = spm_vol(imgs{iFile});
    spmTvol = spm_read_vols(spmThead);
    spmPvol = spmTvol;
    spmPvol = tTest(dof,spmPvol);
    spmPvol = -log10(spmPvol);
    spmPvol = sign(spmTvol) .* spmPvol;
    if iFile < 10
        filename = sprintf('spmSig_000%s.nii',num2str(iFile));
    else 
        filename = sprintf('spmSig_00%s.nii',num2str(iFile));
    end
    filename = fullfile(contrastdir,filename);
    fprintf('Writing %s\n',filename);
    spmPhead = spmThead;
    spmPhead.fname = filename;
    spm_write_vol(spmPhead,spmPvol);
end
