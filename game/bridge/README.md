# Echelon Bridge DLL

This project builds the first-pass Arma extension used by the local
`@EchelonProxy` mod shell.

Primary responsibilities:

- expose required Arma extension entrypoints;
- accept control commands from SQF;
- maintain one local backend session;
- exchange one-line state-sync messages with the authoritative backend;
- cache the last good proxy-state payload for SQF polling.
