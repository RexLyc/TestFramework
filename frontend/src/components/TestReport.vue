<script setup lang="ts">
import { TestGraph } from '@/TestNode';
import { onMounted, watch, ref } from 'vue';
import * as d3 from "d3";

interface HierarchyBaseClass {
  name: String;
}

class HierarchyLeafClass implements HierarchyBaseClass{
  name: String = '';
  value: Number = 1;
}

class HierarchyBranchClass implements HierarchyBaseClass{
  name: String = '';
  children: HierarchyBranchClass[] | HierarchyLeafClass[] = [];

  
}

const timePartition = ref<HierarchyBranchClass>(new HierarchyBranchClass());

const props = defineProps({
    testReportDetail: Object,
});

let node = null;

// 数据可视化
const updatePartition = (testReportDetail:any)=>{
  // timelines 
  console.log(typeof(testReportDetail.timeline.timelineMap));
  timePartition.value.name = 'root';
  timePartition.value.children = [] as HierarchyBranchClass[];
  for(const nodeType in testReportDetail.timeline.timelineMap){
    console.log(nodeType);
    // 新增节点类型
    const newNode = new HierarchyBranchClass();
    newNode.name = nodeType;
    newNode.children = [] as HierarchyBranchClass[];
    timePartition.value.children.push(newNode);
    for(const nodeName in testReportDetail.timeline.timelineMap[nodeType]){
      console.log(nodeName);
      // 新增命名节点
      const newNameNode = new HierarchyBranchClass();
      newNameNode.name = nodeName;
      newNameNode.children = [] as HierarchyLeafClass[];
      newNode.children.push(newNameNode);
      for(const runNodeName in testReportDetail.timeline.timelineMap[nodeType][nodeName].timelines){
        // 新增运行命名节点
        const newRunNameNode = new HierarchyLeafClass();
        newRunNameNode.name = runNodeName;
        newRunNameNode.value = testReportDetail.timeline.timelineMap[nodeType][nodeName].timelines[runNodeName][1]
          -testReportDetail.timeline.timelineMap[nodeType][nodeName].timelines[runNodeName][0];
        newNameNode.children.push(newRunNameNode);
      }
    }
  }
  console.log(timePartition.value);
  node = createParition(timePartition.value);
}

watch(props,()=>{
  console.log(props.testReportDetail);
  if(props.testReportDetail!=null){
    updatePartition(props.testReportDetail);
  } else {
  }
})

const partitionHelper = (data:any) => {
  const root = d3.hierarchy(data)
      .sum((d:any) => d.value)
      .sort((a:any, b:any) => b.value - a.value);
  return d3.partition()
      .size([2 * Math.PI, root.height + 1])
    (root);
}

const width = 800;
const radius = width/6;

const format = ()=>{
  return(
  d3.format(",d")
  )
}

const arc = (radius:any)=>{
  return(
  d3.arc()
      .startAngle((d:any) => d.x0)
      .endAngle((d:any) => d.x1)
      .padAngle((d:any) => Math.min((d.x1 - d.x0) / 2, 0.005))
      .padRadius(radius * 1.5)
      .innerRadius((d:any) => d.y0 * radius)
      .outerRadius((d:any) => Math.max(d.y0 * radius, d.y1 * radius - 1))
  )
}

const createParition = (data:any)=>{
  // delete old
  d3.select('.PieContainer').selectAll('svg').remove();
  // add new
  const svg = d3.select('.PieContainer')
    .append('svg')
    .attr("preserveAspectRatio", "xMidYMid meet")
    .attr("viewBox", [0, 0, width, width])
    .style("font", "12px sans-serif");
  const root = partitionHelper(data);

  root.each((d:any) => d.current = d);

  const g = svg.append("g")
      .attr("transform", `translate(${width / 2},${width / 2})`);

  const color = d3.scaleOrdinal(d3.quantize(d3.interpolateRainbow, data.children.length + 1))

  const path = g.append("g")
    .selectAll("path")
    .data(root.descendants().slice(1))
    .join("path")
      .attr("fill", (d:any) => { while (d.depth > 1) d = d.parent; return color(d.data.name); })
      .attr("fill-opacity", (d:any) => arcVisible(d.current) ? (d.children ? 0.6 : 0.4) : 0)
      .attr("pointer-events", (d:any) => arcVisible(d.current) ? "auto" : "none")

      .attr("d", (d:any) => arc(radius)(d.current));

  path.filter((d:any) => d.children)
      .style("cursor", "pointer")
      .on("click", clicked);

  path.append("title")
      .text((d:any) => `${d.ancestors().map((d:any) => d.data.name).reverse().join("/")}\n${format()(d.value)}`);

  const label = g.append("g")
      .attr("pointer-events", "none")
      .attr("text-anchor", "middle")
      .style("user-select", "none")
    .selectAll("text")
    .data(root.descendants().slice(1))
    .join("text")
      .attr("dy", "0.35em")
      .attr("fill-opacity", (d:any) => +labelVisible(d.current))
      .attr("transform", (d:any) => labelTransform(d.current))
      .text((d:any) => d.data.name);

  const parent = g.append("circle")
      .datum(root)
      .attr("r", radius)
      .attr("fill", "none")
      .attr("pointer-events", "all")
      .on("click", clicked);

  function clicked(event:any, p:any) {
    parent.datum(p.parent || root);

    root.each((d:any) => d.target = {
      x0: Math.max(0, Math.min(1, (d.x0 - p.x0) / (p.x1 - p.x0))) * 2 * Math.PI,
      x1: Math.max(0, Math.min(1, (d.x1 - p.x0) / (p.x1 - p.x0))) * 2 * Math.PI,
      y0: Math.max(0, d.y0 - p.depth),
      y1: Math.max(0, d.y1 - p.depth)
    });

    const t = g.transition().duration(750);
    // Transition the data on all arcs, even the ones that aren’t visible,
    // so that if this transition is interrupted, entering arcs will start
    // the next transition from the desired position.
    path.transition(t)
        .tween("data", (d:any) => {
          const i = d3.interpolate(d.current, d.target);
          return (t:any) => d.current = i(t);
        })
      .filter(function(this: any,d:any) {
        return +this.getAttribute("fill-opacity") || arcVisible(d.target);
      })
        .attr("fill-opacity", (d:any) => arcVisible(d.target) ? (d.children ? 0.6 : 0.4) : 0)
        .attr("pointer-events", (d:any) => arcVisible(d.target) ? "auto" : "none") 

        .attrTween("d", (d:any) => () => arc(radius)(d.current));

    label.filter(function(this: any,d:any) {
        return +this.getAttribute("fill-opacity") || labelVisible(d.target);
      }).transition(t)
        .attr("fill-opacity", (d:any) => +labelVisible(d.target))
        .attrTween("transform", (d:any) => () => labelTransform(d.current));
  }
  
  function arcVisible(d:any) {
    return d.y1 <= 3 && d.y0 >= 1 && d.x1 > d.x0;
  }

  function labelVisible(d:any) {
    return d.y1 <= 3 && d.y0 >= 1 && (d.y1 - d.y0) * (d.x1 - d.x0) > 0.03;
  }

  function labelTransform(d:any) {
    const x = (d.x0 + d.x1) / 2 * 180 / Math.PI;
    const y = (d.y0 + d.y1) / 2 * radius;
    return `rotate(${x - 90}) translate(${y},0) rotate(${x < 180 ? 0 : 180})`;
  }
  return svg.node();
}

const drag = (simulation:any) => {
  
  function dragstarted(event: any, d: any) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
  }
  
  function dragged(event: any, d: any) {
    d.fx = event.x;
    d.fy = event.y;
  }
  
  function dragended(event: any, d: any) {
    if (!event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
  }
  
  return d3.drag()
      .on("start", dragstarted)
      .on("drag", dragged)
      .on("end", dragended);
}

function linkArc(d: any) {
  const r = Math.hypot(d.target.x - d.source.x, d.target.y - d.source.y);
  return `
    M${d.source.x},${d.source.y}
    A${r},${r} 0 0,1 ${d.target.x},${d.target.y}
  `;
}

const chart = (data:any,height:number,color:any,types:any)=> {
  const links = data.links.map((d: any) => Object.create(d));
  const nodes = data.nodes.map((d: any) => Object.create(d));

  const simulation = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(links).id((d: any) => d.id))
      .force("charge", d3.forceManyBody().strength(-400))
      .force("x", d3.forceX())
      .force("y", d3.forceY());

  const svg = d3.select(".TopologyContainer").append("svg")
      .attr("viewBox", [-width / 2, -height / 2, width, height])
      .style("font", "20px sans-serif");

  // Per-type markers, as they don't inherit styles.
  svg.append("defs").selectAll("marker")
    .data(types)
    .join("marker")
      .attr("id", (d: any) => `arrow-${d}`)
      .attr("viewBox", "0 -5 10 10")
      .attr("refX", 15)
      .attr("refY", -0.5)
      .attr("markerWidth", 6)
      .attr("markerHeight", 6)
      .attr("orient", "auto")
    .append("path")
      .attr("fill", color)
      .attr("d", "M0,-5L10,0L0,5");

  const link = svg.append("g")
      .attr("fill", "none")
      .attr("stroke-width", 5)
    .selectAll("path")
    .data(links)
    .join("path")
      .attr("stroke", (d: any) => color(d.type))
      // .attr("marker-end", d => `url(${new URL(`#arrow-${d.type}`, location)})`);

  const node = svg.append("g")
      .attr("fill", "currentColor")
      .attr("stroke-linecap", "round")
      .attr("stroke-linejoin", "round")
    .selectAll("g")
    .data(nodes)
    .join("g")
      .call(drag(simulation));

  node.append("circle")
      .attr("stroke", "white")
      .attr("stroke-width", 1.5)
      .attr("r", 4);

  node.append("text")
      .attr("x", 8)
      .attr("y", "0.31em")
      .text((d: any) => d.id)
    .clone(true).lower()
      .attr("fill", "none")
      .attr("stroke", "white")
      .attr("stroke-width", 3);

  simulation.on("tick", () => {
    link.attr("d", linkArc);
    node.attr("transform", (d: any) => `translate(${d.x},${d.y})`);
  });

  // invalidation.then(() => simulation.stop());

  return svg.node();
}

// Copyright 2021 Observable, Inc.
// Released under the ISC license.
// https://observablehq.com/@d3/tree
function Tree(data:any, { // data is either tabular (array of objects) or hierarchy (nested objects)
  path = null, // as an alternative to id and parentId, returns an array identifier, imputing internal nodes
  id = Array.isArray(data) ? (d:any) => d.id : null, // if tabular data, given a d in data, returns a unique identifier (string)
  parentId = Array.isArray(data) ? (d:any) => d.parentId : null, // if tabular data, given a node d, returns its parent’s identifier
  children = null, // if hierarchical data, given a d in data, returns its children
  tree = d3.tree, // layout algorithm (typically d3.tree or d3.cluster)
  sort = null, // how to sort nodes prior to layout (e.g., (a, b) => d3.descending(a.height, b.height))
  label = null, // given a node d, returns the display name
  title = null, // given a node d, returns its hover text
  link = null, // given a node d, its link (if any)
  linkTarget = "_blank", // the target attribute for links (if any)
  width = 640, // outer width, in pixels
  height = null, // outer height, in pixels
  r = 3, // radius of nodes
  padding = 1, // horizontal padding for first and last column
  fill = "#999", // fill for nodes
  fillOpacity = null, // fill opacity for nodes
  stroke = "#555", // stroke for links
  strokeWidth = 1.5, // stroke width for links
  strokeOpacity = 0.4, // stroke opacity for links
  strokeLinejoin = null, // stroke line join for links
  strokeLinecap = null, // stroke line cap for links
  halo = "#fff", // color of label halo 
  haloWidth = 3, // padding around the labels
  curve = d3.curveBumpX, // curve for the link
} = {}) {

  // If id and parentId options are specified, or the path option, use d3.stratify
  // to convert tabular data to a hierarchy; otherwise we assume that the data is
  // specified as an object {children} with nested objects (a.k.a. the “flare.json”
  // format), and use d3.hierarchy.
  const root = path != null ? d3.stratify().path(path)(data)
      : id != null || parentId != null ? d3.stratify().id(id).parentId(parentId)(data)
      : d3.hierarchy(data, children);

  // Sort the nodes.
  if (sort != null) root.sort(sort);

  // Compute labels and titles.
  const descendants = root.descendants();
  const L = label == null ? null : descendants.map((d:any) => (label as any)(d.data, d));

  // Compute the layout.
  const dx = 10;
  const dy = width / (root.height + padding);
  tree().nodeSize([dx, dy])(root);

  // Center the tree.
  let x0 = Infinity;
  let x1 = -x0;
  root.each((d:any) => {
    if (d.x > x1) x1 = d.x;
    if (d.x < x0) x0 = d.x;
  });

  // Compute the default height.
  (height as any) = height == null ?  x1 - x0 + dx * 2 : height;

  // Use the required curve
  if (typeof curve !== "function") throw new Error(`Unsupported curve`);

  const svg = d3.create("svg")
      .attr("viewBox", [-dy * padding / 2, x0 - dx, width, height])
      .attr("width", width)
      .attr("height", height)
      .attr("style", "max-width: 100%; height: auto; height: intrinsic;")
      .attr("font-family", "sans-serif")
      .attr("font-size", 10);

  svg.append("g")
      .attr("fill", "none")
      .attr("stroke", stroke)
      .attr("stroke-opacity", strokeOpacity)
      .attr("stroke-linecap", strokeLinecap)
      .attr("stroke-linejoin", strokeLinejoin)
      .attr("stroke-width", strokeWidth)
    .selectAll("path")
      .data(root.links())
      .join("path")
        .attr("d", d3.link(curve)
            .x((d:any) => d.y)
            .y((d:any) => d.x));

  const node = svg.append("g")
    .selectAll("a")
    .data(root.descendants())
    .join("a")
      .attr("xlink:href", link == null ? null : (d:any) => (link as any)(d.data, d))
      .attr("target", link == null ? null : linkTarget)
      .attr("transform", (d:any) => `translate(${d.y},${d.x})`);

  node.append("circle")
      .attr("fill", (d:any) => d.children ? stroke : fill)
      .attr("r", r);

  if (title != null) node.append("title")
      .text((d:any) => (title as any)(d.data, d));

  if (L) node.append("text")
      .attr("dy", "0.32em")
      .attr("x", (d:any) => d.children ? -6 : 6)
      .attr("text-anchor", (d:any) => d.children ? "end" : "start")
      .attr("paint-order", "stroke")
      .attr("stroke", halo)
      .attr("stroke-width", haloWidth)
      .text((d:any, i:any) => L[i]);

  return svg.node();
}

interface TreeBaseClass {
  name: string;
}

class TreeParentClass implements TreeBaseClass {
  name: string = '';
  children: TreeBaseClass[] = [];
}

class TreeChildClass implements TreeBaseClass {
  name: string = '';
  size: number = 0;
}

const getTreeNode = (topology:any,nodeFullName:string):TreeBaseClass => {
  //建立该nodeFullName的子树并返回
  const queue: string[] = [];
  if(nodeFullName in topology){
    const parent = new TreeParentClass();
    parent.name = nodeFullName;
    for(const child of topology[nodeFullName]){
      parent.children.push(getTreeNode(topology,child));
    }
    return parent;
  } else {
    const child = new TreeChildClass();
    child.name = nodeFullName;
    return child;
  }
}

const updateTopologyTree = (testReportDetail:any) => {
  // topology转换
  const treeData = new TreeParentClass();
  // 起点
  treeData.name = 'null';
  treeData.children.push(getTreeNode(testReportDetail.topology,'null'));
  const obj = {
    label: (d:any) => d.name,
    title: (d:any, n:any) => `${n.ancestors().reverse().map((d:any) => d.data.name).join(".")}`, // hover text
    width: 1152
  }
  const chart = Tree(treeData, obj)
}

class Link {
  source: string = '';
  target: string = '';
  type:   string = '';
}

const updateTopologyLink = (testReportDetail: any)=>{
  // 转换
  const links:Link[] = [];
  for(const nodeFullName in testReportDetail.topology.generateMap) {
    if(nodeFullName != 'null'){
      for(const targetName of testReportDetail.topology.generateMap[nodeFullName]){
        const temp = new Link();
        temp.source = nodeFullName;
        temp.target = targetName;
        temp.type = 'generate';
        links.push(temp);
      }
    }
  }
  const types = Array.from(new Set(links.map(d => d.type)))
  const color = d3.scaleOrdinal(types, d3.schemeCategory10);
  const data = ({nodes: Array.from(new Set(links.flatMap(l => [l.source, l.target])), id => ({id})), links})
  chart(data,600,color,types);
}

onMounted(()=>{
  if(props.testReportDetail==null){
    return;
  }
  updatePartition(props.testReportDetail);
  // updateTopologyTree(props.testReportDetail);
  updateTopologyLink(props.testReportDetail);
})

const activeNames = ref("1");
</script>

<template>

  <el-tabs v-model="activeNames">
    <el-tab-pane label="运行时间统计" name="1">
      <div class="PieContainer"></div>
    </el-tab-pane>
    <el-tab-pane label="节点生成树" name="2">
      <div class="TopologyContainer"></div>
    </el-tab-pane>
  </el-tabs>

  <!-- <el-collapse v-model="activeNames">
    <el-collapse-item name="1" ex>
      <template #title>
        <el-text class="mx-1" size="default">运行时间统计</el-text>
      </template>
      
    </el-collapse-item>
    <el-collapse-item name="2" ex>
      <template #title>
        <el-text class="mx-1" size="default">节点生成树</el-text>
      </template>
      <div class="TopologyContainer"></div>
    </el-collapse-item>
  </el-collapse> -->
</template>

<style scoped>
/* :deep(.el-popper){
  overflow: hidden ;
} */
.PieContainer,.TopologyContainer {
  margin-left: 25%;
  margin-right: 25%;
  margin-top: 10px;
  margin-bottom: 10px;
}
.el-collapse {
  margin-left: 20px;
}
</style>