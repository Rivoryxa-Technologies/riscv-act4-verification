// SPDX-License-Identifier: MIT
`timescale 1ns/1ps
module mm_ram_timer_tb;
  logic clk=0, rst=0, req=0, we=0;
  logic [31:0] addr=0, wdata=0, rdata, irq;
  logic gnt, valid;
  string scenario;
  logic [63:0] before_value, expected;
  logic [63:0] reference_time=0;
  always @(posedge clk) begin
    if (!rst) reference_time <= 0;
    else if (req && we && addr==32'h0200bff8) reference_time <= {reference_time[63:32],wdata};
    else if (req && we && addr==32'h0200bffc) reference_time <= {wdata,reference_time[31:0]};
    else reference_time <= reference_time+1;
  end
  always #5 clk=~clk;
  mm_ram #(.RAM_ADDR_WIDTH(12), .DBG_ADDR_WIDTH(8), .INSTR_RDATA_WIDTH(32)) dut (
    .clk_i(clk), .rst_ni(rst), .dm_halt_addr_i(32'h1a110800),
    .instr_req_i(1'b0), .instr_addr_i(32'b0), .data_req_i(req),
    .data_addr_i(addr), .data_we_i(we), .data_be_i(4'hf), .data_wdata_i(wdata),
    .data_rdata_o(rdata), .data_rvalid_o(valid), .data_gnt_o(gnt),
    .irq_id_i(5'b0), .irq_ack_i(1'b0), .irq_o(irq), .pc_core_id_i(32'b0)
  );
  // Drive only public bus inputs. Internal state is observed, never forced.
  // A bus write starts on a falling edge and is accepted at the next rising edge.
  task write_word(input logic [31:0] address, input logic [31:0] value);
    @(negedge clk); req=1; we=1; addr=address; wdata=value;
    #1; if (gnt !== 1) $fatal(1,"BUS_HANDSHAKE_FAILED");
    @(posedge clk); #1;
  endtask
  task idle_cycle;
    @(negedge clk); req=0; we=0;
    @(posedge clk); #1;
  endtask
  task require_time(input logic [63:0] value, input string marker);
    if (dut.mtime_q !== value)
      $fatal(1,"%s expected=%016h actual=%016h",marker,value,dut.mtime_q);
  endtask
  task read_timer(input logic [31:0] address, input string marker);
    logic [31:0] want;
    // Drain previous write responses before issuing the read.
    repeat(3) idle_cycle();
    @(negedge clk); req=1; we=0; addr=address;
    #1; if (gnt !== 1) $fatal(1,"BUS_HANDSHAKE_FAILED");
    @(posedge clk); want=(address==32'h0200bff8) ? reference_time[31:0] : reference_time[63:32];
    #1;
    if (valid !== 1) $fatal(1,"READ_RESPONSE_FAILED");
    if (rdata !== want) $fatal(1,"%s expected=%08h actual=%08h",marker,want,rdata);
    $display("BUS_READ addr=%08h expected=%08h actual=%08h",address,want,rdata);
    @(negedge clk); req=0;
  endtask
  initial begin
    if (!$value$plusargs("CASE=%s",scenario)) $fatal(1,"MISSING_CASE_FAILED");
    repeat(3) @(negedge clk); rst=1;
    idle_cycle();
    if (scenario=="smoke") begin
      // Normal low writes away from wrap hide the historical defect.
      write_word(32'h0200bff8,32'd100); require_time(64'd100,"SMOKE_FAILED");
      before_value=dut.mtime_q;
      idle_cycle(); require_time(before_value+1,"SMOKE_FAILED");
      idle_cycle(); require_time(before_value+2,"SMOKE_FAILED");
    end else if (scenario=="low_write_at_carry") begin
      write_word(32'h0200bff8,32'hffffffff);
      // Back-to-back bus write replaces low half exactly when free-run would carry.
      // Untouched high half must remain zero; old RTL incorrectly increments it.
      write_word(32'h0200bff8,32'h00000020);
      require_time(64'h0000000000000020,"LOW_WRITE_CARRY_FAILED");
    end else if (scenario=="high_write_holds_low") begin
      write_word(32'h0200bff8,32'hfffffffe);
      before_value=dut.mtime_q;
      write_word(32'h0200bffc,32'h12345678);
      expected={32'h12345678,before_value[31:0]};
      require_time(expected,"HIGH_WRITE_HOLD_FAILED");
    end else if (scenario=="bus_low_write_at_carry") begin
      write_word(32'h0200bff8,32'hffffffff);
      write_word(32'h0200bff8,32'h20);
      read_timer(32'h0200bffc,"BUS_LOW_CARRY_FAILED");
      read_timer(32'h0200bff8,"BUS_LOW_CARRY_FAILED");
    end else if (scenario=="bus_high_write_holds_low") begin
      write_word(32'h0200bff8,32'd100);
      write_word(32'h0200bffc,32'h12345678);
      read_timer(32'h0200bff8,"BUS_HIGH_HOLD_FAILED");
      read_timer(32'h0200bffc,"BUS_HIGH_HOLD_FAILED");
    end else if (scenario=="carry_without_write") begin
      write_word(32'h0200bff8,32'hffffffff);
      idle_cycle(); require_time(64'h0000000100000000,"FREE_CARRY_FAILED");
    end else if (scenario=="spurious_timer_irq") begin
      // Compare=2^32. A legitimate low-half replacement must not cross this bound.
      write_word(32'h02004004,32'd1);
      write_word(32'h02004000,32'd0);
      write_word(32'h0200bff8,32'hffffffff);
      if (irq[7] !== 0) $fatal(1,"IRQ_SETUP_FAILED");
      write_word(32'h0200bff8,32'h20);
      if (irq[7] !== 0) $fatal(1,"SPURIOUS_TIMER_IRQ_FAILED");
    end else $fatal(1,"UNKNOWN_CASE_FAILED");
    $display("HISTORICAL_PASS case=%s",scenario); $finish;
  end
  initial begin #10000; $fatal(1,"WATCHDOG_FAILED"); end
endmodule
