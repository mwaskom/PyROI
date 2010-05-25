function spm_t2p(concell)
% spm_t2p(contrast cell)
% Function to convert voxels in spmT images from
% t-statistics to -log10(p) values for use in FsFast
% ROI analysis prgrams. Argument can be the name of
% 
%
% Written by Michael Waskom -- mwaskom@mit.edu
% Last updated March 15, 2010

if isa(concell,'char')
   concell = {concell};
end

for iCon = 1:length(concell)
    convert_tmaps(concell{iCon});
end

end

function convert_tmaps(contrastdir)
% Get the list of spmT images
fullimginfo = dir([contrastdir '/spmT*.img']);
for i=1:length(fullimginfo)
    imgs{i} = fullfile(contrastdir,fullimginfo(i).name);
end

% Get the DOF for this paradigm
spmread = spm_vol(imgs{1});
spmstr = spmread.descrip;
parseF = strfind(spmstr,'[') + 1;
parseB = strfind(spmstr,']') - 1;
dof = str2num(spmstr(parseF:parseB));

% Read in each image, convert to -log10(p), and write
for iFile = 1:length(imgs)
    disp(['Reading ' imgs{iFile}]);
    spmThead = spm_vol(imgs{iFile});
    spmTvol = spm_read_vols(spmThead);
    signvol = spmTvol ./ abs(spmTvol);
    spmPvol = spmTvol;
    spmPvol = tTest(dof,spmPvol);
    spmPvol = -log10(spmPvol);
    spmPvol = signvol .* spmPvol;
    if iFile < 10
        filename = ['spmP_000' num2str(iFile) '.nii'];
    else 
        filename = ['spmP_00' num2str(iFile) '.nii'];
    end
    filename = fullfile(contrastdir,filename);
    disp(['Writing ' filename]);
    spmPhead = spmThead;
    spmPhead.fname = filename;
    spm_write_vol(spmPhead,spmPvol);
end

end
