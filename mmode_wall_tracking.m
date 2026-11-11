% Ultrasound RF -> M-mode Arterial Wall Tracking
% ===============================================
% Simulates pulse-echo RF ultrasound reflected from the anterior and posterior
% walls of a pulsating artery, forms an M-mode image (depth vs. slow-time) by
% envelope detection + log compression, tracks the two walls, and recovers the
% arterial distension (diameter) waveform.
%
% This is the core processing chain behind the FI-US-TAG / FIWUS wearable
% blood-pressure work: RF -> envelope -> wall position -> distension.
%
% Run in MATLAB:
%   mmode_wall_tracking
%
% Author: Yasar Aykut Altuntop

clear; close all;

%% --- acquisition parameters ---
c      = 1540;        % speed of sound in tissue [m/s]
fs     = 40e6;        % RF sampling rate [Hz]
f0     = 5e6;         % transducer centre frequency [Hz]
depth  = 20e-3;       % imaging depth [m]
prf    = 500;         % pulse-repetition frequency [Hz] (slow-time)
T      = 4;           % acquisition duration [s]

Nfast  = round(2*depth/c*fs);       % samples per A-line (fast-time)
Nslow  = round(T*prf);              % number of A-lines (slow-time)
z      = (0:Nfast-1)'/fs*c/2;       % depth axis [m]
tslow  = (0:Nslow-1)/prf;           % slow-time axis [s]

%% --- physiological wall motion ---
hr     = 72/60;                      % heart rate [Hz]
d0     = 6e-3;                        % mean anterior-wall depth [m]
diam0  = 6e-3;                        % mean diameter [m]
puls   = 0.35e-3*max(sin(2*pi*hr*tslow),0).^1.5;  % systolic distension [m]
d_ant  = d0 - 0.5*puls;              % anterior wall moves up
d_post = d0 + diam0 + 0.5*puls;      % posterior wall moves down

%% --- synthesize RF frames (Gabor pulse-echo per wall) ---
sigma = 1.5/f0;                      % pulse envelope width [s]
rf = zeros(Nfast, Nslow);
for k = 1:Nslow
    for dwall = [d_ant(k), d_post(k)]
        tau = 2*dwall/c;                       % two-way time of flight
        tt  = (0:Nfast-1)'/fs - tau;
        rf(:,k) = rf(:,k) + exp(-0.5*(tt/sigma).^2).*cos(2*pi*f0*tt);
    end
end
rf = rf + 0.05*randn(size(rf));      % receiver noise

%% --- envelope detection + log compression -> M-mode ---
env  = abs(hilbert(rf));
mmode = 20*log10(env/max(env(:)) + 1e-3);   % [dB]

%% --- wall tracking (two strongest envelope peaks per A-line) ---
ant = zeros(1,Nslow); post = zeros(1,Nslow);
for k = 1:Nslow
    [~, loc] = findpeaks(env(:,k), 'SortStr','descend', 'NPeaks',2, ...
                         'MinPeakDistance', round(2e-3/(c/2)*fs));
    loc = sort(loc);
    ant(k)  = z(loc(1));
    post(k) = z(loc(2));
end
diameter = post - ant;               % arterial diameter waveform [m]

%% --- figures ---
figure;
imagesc(tslow, z*1e3, mmode); colormap(gray); caxis([-40 0]);
hold on; plot(tslow, ant*1e3,'c', tslow, post*1e3,'y','LineWidth',1.2);
xlabel('slow-time [s]'); ylabel('depth [mm]');
title('M-mode with tracked arterial walls'); legend('anterior','posterior');

figure;
plot(tslow, diameter*1e3, 'LineWidth',1.4);
xlabel('time [s]'); ylabel('diameter [mm]');
title('Recovered arterial distension waveform'); grid on;

fprintf('mean diameter  : %.2f mm\n', mean(diameter)*1e3);
fprintf('distension     : %.0f um peak-to-peak\n', (max(diameter)-min(diameter))*1e6);
