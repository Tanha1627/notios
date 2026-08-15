const ENDPOINT = "/graphql";

class GraphQLError extends Error {
  constructor(message, errors) {
    super(message);
    this.errors = errors;
  }
}

async function request(query, variables = {}, token) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(ENDPOINT, {
    method: "POST",
    headers,
    body: JSON.stringify({ query, variables }),
  });

  const json = await res.json();
  if (json.errors && json.errors.length) {
    throw new GraphQLError(json.errors[0].message, json.errors);
  }
  return json.data;
}

export const api = {
  register: ({ email, name, password }) =>
    request(
      `mutation($email:String!,$name:String!,$password:String!){
        register(email:$email,name:$name,password:$password){
          token user{ id email name }
        }
      }`,
      { email, name, password }
    ),

  login: ({ email, password }) =>
    request(
      `mutation($email:String!,$password:String!){
        login(email:$email,password:$password){
          token user{ id email name }
        }
      }`,
      { email, password }
    ),

  me: (token) =>
    request(`{ me { id email name } }`, {}, token),

  myWorkspaces: (token) =>
    request(`{ myWorkspaces { id name ownerId } }`, {}, token),

  userByEmail: (token, email) =>
    request(
      `query($email:String!){ userByEmail(email:$email){ id email name } }`,
      { email },
      token
    ),

  pagePermissions: (token, pageId) =>
    request(
      `query($pageId:String!){ pagePermissions(pageId:$pageId){ id userId role } }`,
      { pageId },
      token
    ),

  createWorkspace: (token, name) =>
    request(
      `mutation($name:String!){ createWorkspace(name:$name){ id name ownerId } }`,
      { name },
      token
    ),

  pages: (token, workspaceId, search) =>
    request(
      `query($workspaceId:String!,$search:String){
        pages(workspaceId:$workspaceId, search:$search){
          id title parentPageId myRole createdAt updatedAt
        }
      }`,
      { workspaceId, search },
      token
    ),

  page: (token, id) =>
    request(
      `query($id:String!){
        page(id:$id){ id title parentPageId myRole workspaceId createdAt updatedAt }
      }`,
      { id },
      token
    ),

  createPage: (token, { workspaceId, title, parentPageId }) =>
    request(
      `mutation($workspaceId:String!,$title:String!,$parentPageId:String){
        createPage(workspaceId:$workspaceId,title:$title,parentPageId:$parentPageId){
          id title parentPageId myRole
        }
      }`,
      { workspaceId, title, parentPageId: parentPageId || null },
      token
    ),

  updatePageTitle: (token, pageId, title) =>
    request(
      `mutation($pageId:String!,$title:String!){
        updatePage(pageId:$pageId,title:$title){ id title }
      }`,
      { pageId, title },
      token
    ),

  deletePage: (token, pageId) =>
    request(`mutation($pageId:String!){ deletePage(pageId:$pageId) }`, { pageId }, token),

  blocks: (token, pageId) =>
    request(
      `query($pageId:String!){
        blocks(pageId:$pageId){ id type content position parentBlockId }
      }`,
      { pageId },
      token
    ),

  createBlock: (token, { pageId, type, content, position }) =>
    request(
      `mutation($pageId:String!,$type:String!,$content:JSON!,$position:Int!){
        createBlock(pageId:$pageId,type:$type,content:$content,position:$position){
          id type content position
        }
      }`,
      { pageId, type, content, position },
      token
    ),

  updateBlock: (token, { blockId, content }) =>
    request(
      `mutation($blockId:String!,$content:JSON){
        updateBlock(blockId:$blockId,content:$content){ id content }
      }`,
      { blockId, content },
      token
    ),

  deleteBlock: (token, blockId) =>
    request(`mutation($blockId:String!){ deleteBlock(blockId:$blockId) }`, { blockId }, token),

  sharePage: (token, { pageId, userId, role }) =>
    request(
      `mutation($pageId:String!,$userId:String!,$role:String!){
        sharePage(pageId:$pageId,userId:$userId,role:$role){ id role userId }
      }`,
      { pageId, userId, role },
      token
    ),

  revokeAccess: (token, { pageId, userId }) =>
    request(
      `mutation($pageId:String!,$userId:String!){ revokeAccess(pageId:$pageId,userId:$userId) }`,
      { pageId, userId },
      token
    ),

  searchContent: (token, workspaceId, query) =>
    request(
      `query($workspaceId:String!,$query:String!){
        searchContent(workspaceId:$workspaceId, query:$query){ id title myRole }
      }`,
      { workspaceId, query },
      token
    ),
};

export { GraphQLError };
