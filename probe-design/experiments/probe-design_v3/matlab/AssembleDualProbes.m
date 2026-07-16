function probeFasta = AssembleDualProbes(targetRegions, spec, readouts, commonRT, fwdSeq, revSeq, probeLen)
% AssembleDualProbes  Assemble ready-to-order oligos with a per-probe dual-barcode.
%
% This is the GENERALIZED core of the EP-ORCA v3 pipeline. It replaces the
% single-readout assembly at the tail of FastaToSeqProbes with a position-aware
% assembler: every probe carries readout1 (the region's primary barcode) and, in
% the fiducial (commonRT) slot, EITHER a second readout (if the probe falls in a
% declared "dual zone") OR the commonRT fiducial placeholder. Any future dual /
% staged / multi-labeling scheme is expressed purely as zone lists in `spec` --
% no change to this function.
%
% Probe layout (120 nt, matches the toolbox convention):
%   5' fwdPrimer(20) - [slot2] - readout1(20) - target(40,rc) - revPrimer(20,rc) 3'
%   slot2 = commonRT(20) fiducial  OR  a second readout(20)  (dual zones)
%
% INPUTS
%   targetRegions : struct array returned by FastaToSeqProbes (2nd output).
%                   Uses .geneName, .sequence (cell of length-L target seqs),
%                   .startPos (probe start offset within the region sequence).
%   spec          : struct array, one entry per region, fields:
%                     .geneName    matches targetRegions(r).geneName
%                     .gStart,.gEnd genomic coords of the region (1-based, incl.)
%                     .wasRevcomp  logical: was the target seq reverse-complemented
%                                  when built (RNA & '-', or DNA & '+')
%                     .r1          primary readout number (into `readouts`)
%                     .zones       struct array of dual zones (may be empty), each:
%                                    .zStart,.zEnd  genomic interval
%                                    .r2   second readout number (>0), or -1 = DROP probe
%   readouts      : fasta struct array; readout N == readouts(N).
%   commonRT      : fiducial handle string (e.g. 'catcaacgccacgatcagct').
%   fwdSeq,revSeq : primer sequences for this modality (strings).
%   probeLen      : probe length in nt (e.g. 40).
%
% OUTPUT
%   probeFasta : struct array with .Header and .Sequence (ready to write/BLAST).

rcFun  = @(s) seqrcomplement(s);
handle = @(n) upper(rcFun(readouts(n).Sequence(1:20)));  % probe-borne readout handle (rc of first 20nt)
fwd    = upper(fwdSeq);
rev    = upper(rcFun(revSeq));
fid    = lower(commonRT);

names = {};
seqs  = {};
for r = 1:numel(targetRegions)
    tr = targetRegions(r);
    si = find(strcmp({spec.geneName}, tr.geneName), 1);
    if isempty(si)
        warning('AssembleDualProbes:noSpec','no spec for region %s -- skipped', tr.geneName);
        continue
    end
    sp     = spec(si);
    r1seq  = handle(sp.r1);
    tseqs  = tr.sequence;
    spos   = tr.startPos;
    if ~iscell(tseqs); tseqs = cellstr(tseqs); end
    for p = 1:numel(tseqs)
        off = double(spos(p));                      % 0/1-based offset into region seq
        % --- genomic center of this probe (for zone testing)
        if sp.wasRevcomp
            gc = sp.gEnd  - off - probeLen/2;        % target seq is reversed vs genome
        else
            gc = sp.gStart + off + probeLen/2;
        end
        % --- resolve the second slot from the zones (first match wins)
        r2 = 0; drop = false;
        for z = 1:numel(sp.zones)
            zn = sp.zones(z);
            if gc >= zn.zStart && gc <= zn.zEnd
                if zn.r2 == -1
                    drop = true;                     % partner of an overlap: discard
                else
                    r2 = zn.r2;                       % carrier: second readout in fiducial slot
                end
                break
            end
        end
        if drop; continue; end
        % --- assemble
        if r2 > 0
            slot2 = handle(r2);
        else
            slot2 = fid;                             % fiducial placeholder
        end
        oligo = [fwd, slot2, r1seq, lower(rcFun(tseqs{p})), rev];
        names{end+1,1} = sprintf('%s__r1-%d__r2-%d__p%04d', tr.geneName, sp.r1, r2, p); %#ok<AGROW>
        seqs{end+1,1}  = oligo;                                                          %#ok<AGROW>
    end
end

if isempty(seqs)
    probeFasta = struct('Header',{},'Sequence',{});
else
    probeFasta = cell2struct([names, seqs]', {'Header','Sequence'});
end
end
