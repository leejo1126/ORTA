%% EP-ORCA v3 probe generation -- generalized dual-labeling pipeline
% Based on S260715_JudeDerek_EP2.m, but generalized so the fiducial slot can
% hold a SECOND readout per probe (dual-barcode), driven by CSV spec tables.
% Tiling/filtering still uses the shared toolbox (FastaToSeqProbes); only the
% barcode assembly is taken over (AssembleDualProbes) so the scheme is data-driven.
%
% Reads (from ..\rebuild\):  coordinates_v3.csv, readout_scheme_v3.csv, dual_barcode_v3.csv
% Writes (to ..\rebuild\probes\): targets/off-target fastas, EP_ORCA_v3_<mod>_probe.fasta
%
% NOTE: this calls shared, read-only toolbox functions on the MATLAB path
% (FastaToSeqProbes, BLAST, WriteFasta, fastaread). Nothing in C:\Shared is modified.
% VERIFY before a full run: (1) FastaToSeqProbes 2nd output is targetRegions with
% .sequence/.startPos/.geneName; (2) startPos indexing base; (3) primer indices.

clc; clear; close all;

%% ---- config -----------------------------------------------------------
projDir   = 'S:\cluade code\EP-ORCA\rebuild\';
outDir    = [projDir 'probes\'];  if ~exist(outDir,'dir'); mkdir(outDir); end
genomeDir = '\\blabserver1\u\GenomeData\GenomeAssemblies\mm10\';
readoutFa = 'U:\Data\Oligos\CommonOligos\v6_Adapters1_readouts001-384_240212.fasta';
fwdFa     = 'U:\Data\Oligos\CommonOligos\FwdPrimers.fasta';
revFa     = 'U:\Data\Oligos\CommonOligos\RevPrimers.fasta';
mmRpts    = 'U:\GenomeData\Mouse\mouseRepeatsForBLAST.fasta';
rnaRpts   = 'U:\GenomeData\Mouse\RNA\mm_rRNA_and_tRNA.fasta';
commonRT  = 'catcaacgccacgatcagct';   % fiducial (P4-405) handle; placeholder for 2nd readout
probeLen  = 40;

% primer indices (from S260715): RNA fwd2/rev3, DNA fwd1/rev4
fwdIdx = struct('RNA',2,'DNA',1);
revIdx = struct('RNA',3,'DNA',4);
% tiling / filter params
minProbes = struct('RNA',40,'DNA',80);
maxProbes = 400;
gcRange = [.35 .65]; specRange = [.7 1]; specMatch = 16;
genomeOTmatch = 16;  genOT = [-1 35];  repeatOTmatch = 13;  threePrimeSpace = 1;
blastKeepMax = 10;   % keep probes with <= this many BLAST hits

%% ---- load -------------------------------------------------------------
global mm10; %#ok<GVMIS>
if isempty(mm10); fprintf('loading mm10 (slow)...\n'); mm10 = fastaread([genomeDir 'mm10.fasta']); end
readouts = fastaread(readoutFa);
fwdP = fastaread(fwdFa);
revP = fastaread(revFa);
coords = readtable([projDir 'coordinates_v3.csv'],  'TextType','string');
scheme = readtable([projDir 'readout_scheme_v3.csv'],'TextType','string');
dualbc = readtable([projDir 'dual_barcode_v3.csv'],  'TextType','string');
chrNames = string({mm10.Header});

%% ---- per-modality pipeline -------------------------------------------
for modality = ["RNA","DNA"]
    mod   = char(modality);
    isDNA = strcmp(mod,'DNA');
    fprintf('\n===== %s =====\n', mod);

    % features present in this modality
    if isDNA
        feats = coords;                                    % every feature has a DNA probe
    else
        feats = coords(coords.rna_probe=="yes", :);        % RNA only where rna_probe==yes
    end

    % build target fasta + region spec
    tgtFile = [outDir sprintf('targets_%s.fasta', mod)];
    if exist(tgtFile,'file'); delete(tgtFile); end
    spec = struct('geneName',{},'gStart',{},'gEnd',{},'wasRevcomp',{},'r1',{},'zones',{});
    for i = 1:height(feats)
        nm = char(feats.name(i));  chr = char(feats.chr(i));  strand = char(feats.strand(i));
        if isDNA; gS = feats.dna_start(i); gE = feats.dna_end(i);
        else;     gS = feats.rna_start(i); gE = feats.rna_end(i); end
        seq = mm10(chrNames==chr).Sequence(gS:gE);
        wasRC = (~isDNA && strand=='-') || (isDNA && strand=='+');   % strand rule
        if wasRC; seq = seqrcomplement(seq); end
        WriteFasta(tgtFile, [mod '_' nm], seq, 'Append', true);

        r1    = lookupReadout(scheme, [mod '_' nm]);
        zones = buildZones(dualbc, nm, mod, isDNA);
        spec(end+1) = struct('geneName',[mod '_' nm], 'gStart',gS, 'gEnd',gE, ...
                             'wasRevcomp',wasRC, 'r1',r1, 'zones',zones); %#ok<SAGROW>
    end

    % off-target fasta: genome with all target loci masked to 'n'
    otFile = [outDir sprintf('otSeqs_%s.fasta', mod)];
    if ~exist(otFile,'file'); buildOffTarget(mm10, chrNames, feats, isDNA, otFile); end

    % tile + filter (toolbox); we use only the targetRegions output, not its assembly
    if isDNA
        [~, targetRegions] = FastaToSeqProbes(tgtFile, [], ...
            'fwdPrimerIndex',fwdIdx.DNA, 'revPrimerIndex',revIdx.DNA, ...
            'repeatFasta',mmRpts, 'repeatOTmatch',repeatOTmatch, ...
            'minProbesPerRegion',minProbes.DNA, 'maxProbesPerRegion',maxProbes, ...
            'specRange',specRange, 'specMatch',specMatch, 'gcRange',gcRange, ...
            'threePrimeSpace',threePrimeSpace, 'genomeOffTarget',otFile, ...
            'genomeOTmatch',genomeOTmatch, 'genOTrange',genOT);
    else
        [~, targetRegions] = FastaToSeqProbes(tgtFile, [], ...
            'fwdPrimerIndex',fwdIdx.RNA, 'revPrimerIndex',revIdx.RNA, ...
            'repeatFasta',rnaRpts, 'repeatOTmatch',repeatOTmatch, ...
            'minProbesPerRegion',minProbes.RNA, 'maxProbesPerRegion',maxProbes, ...
            'specRange',specRange, 'specMatch',specMatch, 'gcRange',gcRange, ...
            'threePrimeSpace',threePrimeSpace);
    end

    % custom dual-barcode assembly
    fwdSeq = fwdP(fwdIdx.(mod)).Sequence;
    revSeq = revP(revIdx.(mod)).Sequence;
    probeFasta = AssembleDualProbes(targetRegions, spec, readouts, commonRT, fwdSeq, revSeq, probeLen);
    fprintf('%s: assembled %d oligos\n', mod, numel(probeFasta));

    % BLAST prune against the genome (as S260715)
    [~,~,hits] = BLAST(probeFasta, [genomeDir 'mm10.fasta'], 'numThreads',40, 'wordSize',25, 'verbose',false);
    probeFasta(hits > blastKeepMax) = [];
    fprintf('%s: %d oligos after BLAST prune\n', mod, numel(probeFasta));

    % write
    outFa = [outDir sprintf('EP_ORCA_v3_%s_probe.fasta', mod)];
    if exist(outFa,'file'); delete(outFa); end
    WriteFasta(outFa, probeFasta, [], 'Append', false);
    fprintf('%s: wrote %s\n', mod, outFa);
end

% archive this script alongside outputs
copyfile([mfilename('fullpath') '.m'], [outDir mfilename '.m']);
disp('---- probe generation complete ----');


%% ======================= local functions ==============================
function r = lookupReadout(scheme, featureName)
% readout_number for a feature (e.g. 'DNA_E_Nanog') from readout_scheme_v3
    idx = find(scheme.feature == string(featureName), 1);
    if isempty(idx)
        error('lookupReadout:missing','no readout for %s in scheme', featureName);
    end
    r = scheme.readout_number(idx);
end

function zones = buildZones(dualbc, featName, mod, isDNA) %#ok<INUSD>
% Build the dual-zone list for one feature+modality from dual_barcode_v3.
%   carrier rows -> a zone with r2 = readout_secondary (probe gets 2nd readout)
%   partner rows with partner_action=='drop' -> a zone with r2 = -1 (probe discarded)
    zones = struct('zStart',{},'zEnd',{},'r2',{});
    rows = dualbc(dualbc.modality == string(mod), :);
    for j = 1:height(rows)
        if rows.carrier(j) == string(featName)
            zones(end+1) = struct('zStart',rows.region_start(j), 'zEnd',rows.region_end(j), ...
                                  'r2', rows.readout_secondary(j)); %#ok<AGROW>
        elseif rows.partner(j) == string(featName) && rows.partner_action(j) == "drop"
            zones(end+1) = struct('zStart',rows.region_start(j), 'zEnd',rows.region_end(j), ...
                                  'r2', -1); %#ok<AGROW>
        end
    end
end

function buildOffTarget(mm10, chrNames, feats, isDNA, otFile)
% Write a genome fasta with every target locus masked to 'n', for OT filtering.
    if exist(otFile,'file'); delete(otFile); end
    chrs = unique(feats.chr);
    for c = 1:numel(chrs)
        chr = char(chrs(c));
        s = mm10(chrNames==chr).Sequence;
        f = feats(feats.chr==chrs(c), :);
        for i = 1:height(f)
            if isDNA; a = f.dna_start(i); b = f.dna_end(i);
            else;     a = f.rna_start(i); b = f.rna_end(i); end
            s(a:b) = 'n';
        end
        WriteFasta(otFile, chr, s, 'Append', true);
    end
end
