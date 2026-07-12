class fifo_env extends uvm_env;

    fifo_agent agent;
    fifo_scoreboard scoreboard;
    fifo_coverage coverage;

    `uvm_component_utils(fifo_env)

    function new(string name = "fifo_env", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        agent = fifo_agent::type_id::create("agent", this);
        scoreboard = fifo_scoreboard::type_id::create("scoreboard", this);
        coverage = fifo_coverage::type_id::create("coverage", this);
    endfunction

    virtual function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);
        agent.monitor.ap.connect(scoreboard.item_export);
        agent.monitor.ap.connect(coverage.analysis_export);
    endfunction

endclass