// Stand-in for the team's integration EXEs, which run nonstop on private VMs.
// It does no real work: it writes a heartbeat line every 10 seconds so you can
// see it is running. Its purpose is to give the pipeline a .NET program to
// publish and deploy to the VM.
//
// Usage:
//   Integration.exe            run forever, appending to heartbeat.log
//   Integration.exe --health   print OK and exit 0 (used by deploy/deploy-vm.ps1)

if (args.Contains("--health"))
{
    Console.WriteLine("OK");
    return 0;
}

Console.WriteLine("Integration started");
while (true)
{
    File.AppendAllText(Path.Combine(AppContext.BaseDirectory, "heartbeat.log"), $"{DateTime.UtcNow:o} alive\n");
    Thread.Sleep(10000);
}
