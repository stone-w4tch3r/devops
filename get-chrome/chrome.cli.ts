#!/usr/bin/env node
import { Command } from 'commander';
import { resolveChromeExecutable } from './chrome.js';

const program = new Command();

program
    .name('chrome')
    .description(
        'Ensure Chrome for Testing is installed via @puppeteer/browsers and emit its executable path.'
    )
    .action(() => {
        try {
            const chromePath = resolveChromeExecutable();
            const payload = { path: chromePath };
            const output = JSON.stringify(payload, null, 2);
            console.log(output);
        } catch (error) {
            const message =
                error instanceof Error ? error.message : String(error);
            const payload = { error: message };
            const output = JSON.stringify(payload, null, 2);
            console.log(output);
            process.exitCode = 1;
        }
    });

program.parse(process.argv);
