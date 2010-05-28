function func_roi_outlier(databasefile,thresh)
% func_roi_outlier(databasefile,threshold)
% Outlier detection for NiPyRoi database
% More documentation to come
%
% Written by Michael Waskom - mwaskom@mit.edu
% Last updated March 19, 2010

% Print usage
if nargin==0,fprintf('\n\tfunc_roi_outlier(databasefile,thresh)\n\n');return,end

% Set the default threshold
if ~exist('thresh','var'), thresh = 3.0; end

par = strfind(databasefile,'/');
if par
    homeDir = databasefile(1:par(length(par)));
else
    homeDir = '.';
end

% Figure out how to name the files
parse = strfind(databasefile,'_roidata_') + 8;
fnpre = databasefile(par(length(par))+1:parse);
fnsuf = databasefile(parse:length(databasefile));

sfName = [fnpre 'outliers-z' num2str(thresh) fnsuf];
wnName = [fnpre 'winsorized-z' num2str(thresh) fnsuf];
trName = [fnpre 'trimmed-z' num2str(thresh) fnsuf];

% Read in the database and set up a structure
disp('Reading ROI database');
roi = importdata(databasefile);

roi.head = roi.textdata(1,4:size(roi.textdata,2));
roi.subs = roi.textdata(2:size(roi.textdata,1),1);
roi.grps = roi.textdata(2:size(roi.textdata,1),2);
roi.rois = roi.textdata(2:size(roi.textdata,1),3);


disp('Running outlier check');

grpSet = unique(roi.grps);
roiSet = unique(roi.rois);

nInGrp = zeros(length(grpSet),1);
grpCel = cell(length(grpSet),1);

count = ones(length(grpSet));
for iSub = 1:length(roi.grps)
    for iGrp = 1:length(grpSet)
        if roi.grps{iSub} == grpSet{iGrp}
            nInGrp(iGrp,1) = nInGrp(iGrp,1) + 1;
            grpCel{iGrp}{count(iGrp)} = roi.subs{iSub};
            count(iGrp) = count(iGrp) + 1;
        end
    end
end

for iGrp = 1:length(grpSet)
    grpCel{iGrp} = unique(grpCel{iGrp});
end

nInGrp = nInGrp ./ length(roiSet);
dataL = size(roi.data,1);
dataW = size(roi.data,2);

outSum = {};
outCnt = 1;
for iRoi = 1:length(roiSet)
    for iGrp = 1:length(grpSet)
        dataMat = zeros(nInGrp(iGrp),dataW);
        dataKey = zeros(nInGrp(iGrp),1);
        dataRow = 1;
        for iRow = 1:dataL
            if strcmp(roi.rois(iRow),roiSet(iRoi)) && ...
                    strcmp(roi.grps(iRow),grpSet(iGrp))
                dataMat(dataRow,:) = roi.data(iRow,:);
                dataKey(dataRow,1) = iRow;
                dataSub(dataRow,1) = roi.subs(iRow);
                dataRoi(dataRow,1) = roi.rois(iRow);
                dataRow = dataRow + 1;
            end
        end
        for iCon = 1:dataW
            if ~any(findstr(roi.head{iCon},'voxel'))
                mu = mean(dataMat(:,iCon));
                sd = std(dataMat(:,iCon));
                Z = (dataMat(:,iCon) - mu) ./ sd;
                for iRow = 1:size(dataMat,1)
                    if abs(Z(iRow)) > thresh
                        outSum{outCnt,1} = dataSub{iRow};
                        outSum{outCnt,2} = roi.head{iCon};
                        outSum{outCnt,3} = dataRoi{iRow};
                        outSum{outCnt,4} = Z(iRow);
                        outSum{outCnt,5} = dataKey(iRow,1);
                        outSum{outCnt,6} = iCon;
                        outSum{outCnt,7} = ...
                            mu+(sign(Z(iRow)).*(thresh).*(sd));
                        outCnt = outCnt + 1;
                    end
                end
            end
        end
    end
end

sFile = fopen(fullfile(homeDir,'outliers',sfName),'w');
fprintf(sFile,'%s\t','Subject','Condition','ROI','Z-score','i','j',...
    'Winsor-value');
fprintf(sFile,'\n');
for iLine = 1:size(outSum,1);
    fprintf(sFile,'%s\t%s\t%s\t%f\t%d\t%d\t%f\t\n',...
        outSum{iLine,1},outSum{iLine,2},outSum{iLine,3},...
        outSum{iLine,4},outSum{iLine,5},outSum{iLine,6},...
        outSum{iLine,7});
end
fclose(sFile);

winsData = roi.data;
trimData = roi.data;


for iOut = 1:size(outSum,1)
    i = outSum{iOut,5};
    j = outSum{iOut,6};
    winsData(i,j) = outSum{iOut,7};
    trimData(i,j) = NaN;
end

disp('Winsorizing outliers');
disp('Trimming outliers');
wFile = fopen(fullfile(homeDir,'winsor_databases',wnName),'w');
tFile = fopen(fullfile(homeDir,'trimmed_databases',trName),'w');

files = {wFile,tFile};
source = {winsData,trimData};
for iFile = 1:length(files)
    fprintf(files{iFile},'%s\t%s\t%s\t','Subject','Group','ROI');
    for iHead = 1:length(roi.head)
        fprintf(files{iFile},'%s\t',roi.head{iHead});
    end
    fprintf(files{iFile},'\n');
    for i = 1:size(roi.data,1)
        fprintf(files{iFile},'%s\t',roi.subs{i},...
            roi.grps{i},...
            roi.rois{i});
        for j = 1:size(roi.data,2)
            fprintf(files{iFile},'%f\t',source{iFile}(i,j));
        end
        fprintf(files{iFile},'\n');
    end
    fclose(files{iFile});
end
