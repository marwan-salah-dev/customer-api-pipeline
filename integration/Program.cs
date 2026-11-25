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
