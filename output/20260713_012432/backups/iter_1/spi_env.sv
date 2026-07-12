class spi_env extends uvm_env;

    spi_agent agent;
    spi_scoreboard scoreboard;
    spi_coverage coverage;

    `uvm_component_utils(spi_env)

    function new(string name = "spi_env", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        agent = spi_agent::type_id::create("agent", this);
        scoreboard = spi_scoreboard::type_id::create("scoreboard", this);
        coverage = spi_coverage::type_id::create("coverage", this);
    endfunction

    virtual function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);
        agent.monitor.ap.connect(scoreboard.item_export);
        agent.monitor.ap.connect(coverage.analysis_export);
    endfunction

endclass